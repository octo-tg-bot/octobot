import gettext
import html
import logging
import os
import shlex
from uuid import uuid4

import telegram

import octobot
import octobot.exceptions
from octobot.classes import UpdateType
from octobot.database import Database
from octobot.utils import add_photo_to_text
from settings import Settings

logger = logging.getLogger("Context")


def generate_inline_entry(uuid):
    return f"inline:{uuid}"


def generate_id():
    return uuid4().hex[:16]


def create_keyboard_id():
    key_exists = 1
    while key_exists == 1:
        uuid = str(generate_id())
        key_exists = Database.redis.exists(generate_inline_entry(uuid))
    return uuid


def create_inline_button_id(kbd_id):
    key_exists = 1
    while key_exists == 1:
        uuid = str(generate_id())
        key_exists = Database.redis.hexists(kbd_id, uuid)
    return uuid


def encode_callback_data(callback_data, keyboard_id):
    uuid_kbd = keyboard_id
    uuid = create_inline_button_id(uuid_kbd)
    octobot.Database.redis.hset(generate_inline_entry(uuid_kbd), uuid, callback_data)
    data = f"{uuid_kbd}:{uuid}"
    logger.debug(f"{callback_data} -> {data}")
    return data


def rebuild_inline_markup(reply_markup, context):
    if isinstance(reply_markup, telegram.InlineKeyboardMarkup):
        if octobot.Database.redis is None:
            return telegram.InlineKeyboardMarkup.from_button(
                telegram.InlineKeyboardButton(text=context.localize("Buttons are not available due to database error"),
                                              callback_data="nothing:")
            ), None
        else:
            new_markup = []
            kbd_id = create_keyboard_id()
            for row in reply_markup.inline_keyboard:
                new_row = []
                for button in row:
                    if button.callback_data is not None:
                        new_row.append(telegram.InlineKeyboardButton(text=button.text,
                                                                     callback_data=encode_callback_data(
                                                                         callback_data=button.callback_data,
                                                                         keyboard_id=kbd_id)))
                    else:
                        new_row.append(button)
                new_markup.append(new_row)
            octobot.Database.redis.expire(generate_inline_entry(kbd_id), 60 * 60 * 24 * 7)
            return telegram.InlineKeyboardMarkup(new_markup), kbd_id
    else:
        return reply_markup, None


def decode_inline(data, message_id):
    data = data.split(":")
    keyboard_data = "invalid:"
    if len(data) == 2:
        kbd_uuid, button_uuid = data
        db_res = Database.redis.hget(generate_inline_entry(kbd_uuid), button_uuid)
        og_message_id = Database.redis.hget(generate_inline_entry(kbd_uuid), "msg_id")
        logger.debug(f"Original message: {og_message_id} | Current message: {message_id}")
        if db_res is not None:
            if message_id is not None and og_message_id.decode() != str(message_id):
                keyboard_data = "smartass:"
            else:
                Database.redis.delete(generate_inline_entry(kbd_uuid))
                keyboard_data = db_res.decode()
    logger.debug(f"{data} -> {keyboard_data}")
    return keyboard_data


def set_msg_id(message, kbd_id):
    kbd_id = generate_inline_entry(kbd_id)
    logger.debug("Setting message id in redis for keyboard %s", kbd_id)
    logger.debug("exists %s", octobot.Database.redis.exists(kbd_id))
    octobot.Database.redis.hset(kbd_id, "msg_id", str(message.message_id))
    logger.debug("expire result %s",
                 octobot.Database.redis.expire(kbd_id, 60 * 60 * 24 * 7))


class Context:
    """
    Context class. It provides, well, context.

    :param update: Update to create context from
    :type update: :class:`telegram.Update`
    :var user: User class
    :vartype user: :class:`telegram.User`
    :var user_db: Per-user key-value database
    :vartype user_db: :class:`octobot.database.RedisData`
    :var chat: Chat class, can be None in case of inline queries
    :vartype chat: :class:`telegram.Chat`
    :var chat_db: Per-chat key-value database
    :vartype chat_db: :class:`octobot.database.RedisData`
    :var locale: User/Chat locale
    :vartype locale: :class:`str`
    :var update_type: Type of update
    :vartype update_type: :class:`octobot.UpdateType`
    :var query: Command query
    :vartype query: :class:`str`
    :var args: Command arguments, parsed like sys.argv
    :vartype args: :class:`list`
    :var update: Original update
    :vartype update: :class:`telegram.Update`
    """
    _plugin = "unknown"

    def __init__(self, update: telegram.Update, bot):
        self.locale = "en"
        self.bot = bot
        self.update = update
        self.user = update.effective_user
        if self.user is not None:
            self.user_db = Database[self.user.id]
        else:
            self.user_db = None
        self.chat = update.effective_chat
        if self.chat is None and self.user is not None:
            self.chat = self.user
        self.chat_db = Database[self.chat.id]
        if update.inline_query:
            self.text = update.inline_query.query
            self.update_type = UpdateType.inline_query
        elif update.callback_query:
            msg_id = None
            if update.effective_message is not None:
                msg_id = self.update.effective_message.message_id
                logger.debug("Incoming inline button message id is %s.", msg_id)
            self.text = decode_inline(update.callback_query.data, msg_id)
            self.update_type = UpdateType.button_press
        elif update.message:
            if update.message.caption is not None:
                self.text = update.message.caption
            else:
                self.text = update.message.text
            self.update_type = UpdateType.message
        else:
            raise octobot.exceptions.UnknownUpdate("Failed to determine update type for update %s", update.to_dict())
        if self.text is None:
            self.text = ''
        self.query = " ".join(self.text.split(" ")[1:])
        self.args = shlex.split(self.query)

    def reply(self, text, photo_url=None, reply_to_previous=False, reply_markup=None, parse_mode=None, no_preview=False,
              title=None, to_pm=False):
        """
        Replies to a message/shows a popup in inline keyboard/sends out inline query result

        :param text: Text to send
        :type text: :class:`str`
        :param photo_url: Photo URLs, with best quality descending to worst
        :type photo_url: :class:`list`, optional
        :param reply_to_previous: If bot should reply to reply of trigger message, defaults to False. *We need to go deeper*
        :type reply_to_previous: :class:`bool`, optional
        :param reply_markup: Telegram reply markup
        :type reply_markup: :class:`telegram.ReplyMarkup`, optional
        :param parse_mode: Parse mode of messages. Become 'html' if photo_url is passed. Available values are `markdown`, `html` and None
        :type parse_mode: :class:`str`, optional
        :param no_preview: Should the webpage preview be disabled. Defaults to `False`, becomes `False` if `photo_url` is passed
        :type no_preview: :class:`bool`, optional
        :param title: Title of message for inline mode, defaults to first line of `text`
        :type title: :class:`str`, optional
        :param to_pm: If message should be sent into user PM
        :type to_pm: :class:`bool`
        """
        reply_markup, kbd_id = rebuild_inline_markup(reply_markup, self)
        if photo_url:
            if parse_mode is None or parse_mode.lower() != "html":
                parse_mode = "html"
                text = html.escape(text)
            text = add_photo_to_text(text, photo_url)
        if title is None:
            title = self.text[:20]
        if self.update_type == UpdateType.message or to_pm:
            if reply_to_previous and (self.update.message.reply_to_message is not None):
                target_msg: telegram.Message = self.update.message.reply_to_message
            else:
                target_msg: telegram.Message = self.update.message
            if to_pm:
                message = self.bot.send_message(chat_id=self.user.id, text=text, parse_mode=parse_mode,
                                                reply_markup=reply_markup, disable_web_page_preview=no_preview)
            else:
                message = target_msg.reply_text(text=text,
                                                parse_mode=parse_mode,
                                                reply_markup=reply_markup,
                                                disable_web_page_preview=no_preview)
            if kbd_id is not None:
                set_msg_id(message, kbd_id)
        elif self.update_type == UpdateType.inline_query:
            inline_content = telegram.InputTextMessageContent(
                text,
                parse_mode=parse_mode,
                disable_web_page_preview=no_preview
            )
            if photo_url is None:
                result = telegram.InlineQueryResultArticle(self.update.inline_query.query,
                                                           title=title,
                                                           description=text.split("\n")[0],
                                                           input_message_content=inline_content,
                                                           reply_markup=reply_markup)
            else:
                result = telegram.InlineQueryResultPhoto(self.update.inline_query.query,
                                                         photo_url=photo_url,
                                                         thumb_url=photo_url,
                                                         title=title,
                                                         description=text.split("\n")[0],
                                                         input_message_content=inline_content)
            self.update.inline_query.answer([result], cache_time=(360 if Settings.production else 0))
        elif self.update_type == UpdateType.button_press:
            self.update.callback_query.answer(text)

    def edit(self, text=None, photo_url=None, reply_markup=None, parse_mode=None):
        """
        Edits message. Works only if update_type == :obj:`UpdateType.button_press`

        :param text: Text to replace with
        :type text: :class:`str`
        :param photo_url: Photo URLs, with best quality descending to worst
        :type photo_url: :class:`list`, optional
        :param reply_markup: Telegram reply markup
        :type reply_markup: :class:`telegram.ReplyMarkup`, optional
        :param parse_mode: Parse mode of messages. Become 'html' if photo_url is passed. Available values are `markdown`, `html` and None
        :type parse_mode: :class:`str`, optional
        """
        reply_markup, kbd_id = rebuild_inline_markup(reply_markup, self)
        if photo_url:
            if parse_mode is None or parse_mode.lower() != "html":
                parse_mode = "html"
                text = html.escape(text)
            text = add_photo_to_text(text, photo_url)
        if text is not None:
            self.update.callback_query.edit_message_text(
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        elif reply_markup is not None:
            logger.debug("updating reply markup to %s", reply_markup)
            self.update.callback_query.edit_message_reply_markup(reply_markup)
        if kbd_id is not None and self.update.effective_message is not None:
            set_msg_id(kbd_id=kbd_id, message=self.update.effective_message)

    def localize(self, text: str) -> str:
        """
        Localize string according to user-set localization

        :param text: String to translate
        :type text: :class:`str`
        :return: Localized string
        :rtype: :class:`str`
        """
        chat_locale = octobot.localization.get_chat_locale(self.update)
        gt = gettext.translation("messages", localedir="locales", languages=[chat_locale], fallback=True)
        gt.install()

        return gt.gettext(text)
