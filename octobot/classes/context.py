import gettext
import html
import logging
import re
import shlex
from functools import wraps
from uuid import uuid4

import babel
import telegram
from telegram import InputMediaPhoto

import octobot
import octobot.exceptions
from octobot.classes import UpdateType
from octobot import database

Database = database.Database
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


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return html.unescape(cleantext)


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


def decode_inline(data):
    data = data.split(":")
    keyboard_data = "invalid:"
    if len(data) == 2 and Database.redis is not None:
        kbd_uuid, button_uuid = data
        db_res = Database.redis.hget(generate_inline_entry(kbd_uuid), button_uuid)
        if db_res is not None:
            keyboard_data = db_res.decode()
    logger.debug(f"{data} -> {keyboard_data}")
    return keyboard_data


def pluginfo_kwargs(field_name):
    def decorator(function):
        @wraps(function)
        def call_func(self, *args, **kwargs):
            plugin = self._plugin
            kw = getattr(plugin, field_name).copy()
            kw.update(kwargs)
            return function(self, *args, **kw)

        return call_func

    return decorator


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
    :var reply_to_message: Reply_to_message equivalent in Context form
    :vartype reply_to_message: :class:`octobot.Context`, optional
    :var update: Original update
    :vartype update: :class:`telegram.Update`
    """
    _plugin = "unknown"
    _handler = "unknown"
    reply_to_message = None
    text = None
    replied = False
    message = None
    called_command = None
    user: telegram.User
    chat: telegram.Chat

    def __init__(self, update: telegram.Update, bot: "octobot.OctoBot", message: telegram.Message = None):
        # TODO: Move class creation into from_update and from_reply functions cause this is a mess
        self.locale = "en"
        self.bot = bot
        self.update = update
        self.locale = octobot.localization.get_chat_locale(self.update)
        self.locale = babel.Locale.parse(self.locale, sep="-")
        self.user = update.effective_user
        if self.user is not None:
            self.user_db = Database[self.user.id]
        else:
            self.user_db = None
        self.chat = update.effective_chat
        if self.chat is None and self.user is not None:
            self.chat_db = Database[self.user.id]
        if self.chat is not None:
            self.chat_db = Database[self.chat.id]
        self.kbd_id = None
        is_reply = message is not None
        if message is None and update.message is not None:
            message = update.message
        if update.inline_query:
            self.text = update.inline_query.query
            self.update_type = UpdateType.inline_query
        elif update.callback_query:
            self.kbd_id = update.callback_query.data.split(":")[0]
            self.text = decode_inline(update.callback_query.data)
            self.update_type = UpdateType.button_press
        elif message:
            if message.caption is not None:
                self.text = message.caption
            else:
                self.text = message.text
            self.update_type = UpdateType.message
            if octobot.Database.redis is not None and not is_reply:
                octobot.Database.redis.set(octobot.utils.generate_edit_id(self.update.message), 0)
                octobot.Database.redis.expire(octobot.utils.generate_edit_id(self.update.message), 30)
            if message.reply_to_message:
                self.reply_to_message = Context(update, bot, update.message.reply_to_message)
        elif update.edited_message:
            if octobot.Database.redis is None:
                raise octobot.StopHandling
            else:
                self.update.message = self.update.edited_message
                if octobot.Database.redis.exists(octobot.utils.generate_edit_id(self.update.message)):
                    self.edit_tgt = int(octobot.Database.redis.get(octobot.utils.generate_edit_id(self.update.message)))
                    if self.edit_tgt == 0:
                        logger.debug("Not handling update %s cause invalid edit target", update.update_id)
                        raise octobot.StopHandling
                    octobot.Database.redis.delete(octobot.utils.generate_edit_id(self.update.message))
                    self.update_type = UpdateType.edited_message
                    if update.message.caption is not None:
                        self.text = update.message.caption
                    else:
                        self.text = update.message.text
                else:
                    logger.debug("Not handling update %s cause not available in database", update.update_id)
                    raise octobot.StopHandling
                logger.debug("edit target = %s", self.edit_tgt)
        elif update.chosen_inline_result:
            self.update_type = UpdateType.chosen_inline_result
            self.text = update.chosen_inline_result.query
        else:
            raise octobot.exceptions.UnknownUpdate("Failed to determine update type for update %s", update.to_dict())
        if self.text is None:
            self.text = ''
        logger.debug("update type for id %s is %s", self.update.update_id, self.update_type)
        self.query = " ".join(self.text.split(" ")[1:])
        try:
            self.args = shlex.split(self.query)
        except ValueError:
            self.args = self.query.split(" ")

    @pluginfo_kwargs("reply_kwargs")
    def reply(self, text, photo_url=None, reply_to_previous=False, reply_markup=None, parse_mode=None, no_preview=False,
              title=None, to_pm=False, failed=False, editable=True, inline_description=None, photo_primary=False):
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
        :param failed: Pass :obj:`True` if command failed to execute. defaults to :obj:`False`
        :type failed: :class:`bool`, optional
        :param editable: Pass :obj:`False` if you want your command NOT to be editable, defaults to :obj:`True`
        :type editable: :class:`bool`, optional
        :param inline_description: Description for inline mode, optional, defaults to first 400 symbols of `text`
        :type inline_description: :class:`str`
        """
        self.replied = True
        reply_markup, kbd_id = rebuild_inline_markup(reply_markup, self)
        if photo_url and not photo_primary:
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
            kwargs = dict(chat_id=target_msg.chat_id, parse_mode=parse_mode,
                          reply_markup=reply_markup, disable_web_page_preview=no_preview,
                          reply_to_message_id=target_msg.message_id)
            if to_pm:
                kwargs["chat_id"] = self.user.id
                del kwargs["reply_to_message_id"]
            if photo_url and photo_primary:
                try:
                    if "disable_web_page_preview" in kwargs: del kwargs["disable_web_page_preview"]
                    message = self.bot.send_photo(caption=text, photo=photo_url[0], **kwargs)
                except telegram.error.TelegramError:
                    if parse_mode.lower() != 'html':
                        text = html.escape(text)
                    text = f'<b><a href="{photo_url[0]}">Link to image</a></b>\n\n' + text
                    message = self.bot.send_photo(caption=text, photo=Settings.no_image, **kwargs)
            else:
                message = self.bot.send_message(text=text, **kwargs)

            if octobot.Database.redis is not None and editable:
                octobot.Database.redis.set(octobot.utils.generate_edit_id(self.update.message), message.message_id)
                octobot.Database.redis.expire(octobot.utils.generate_edit_id(self.update.message), 30)
            self.edit_tgt = message.message_id
            return message
        elif self.update_type == UpdateType.edited_message and octobot.Database.redis is not None:
            return self.edit(text=text, photo_url=photo_url, reply_markup=reply_markup, parse_mode=parse_mode)
        elif self.update_type == UpdateType.inline_query:
            inline_content = telegram.InputTextMessageContent(
                text,
                parse_mode=parse_mode,
                disable_web_page_preview=no_preview
            )
            result = telegram.InlineQueryResultArticle(self.update.inline_query.query,
                                                       title=title,
                                                       description=cleanhtml(text)[
                                                                   :500] if inline_description is None else inline_description,
                                                       input_message_content=inline_content,
                                                       reply_markup=reply_markup,
                                                       thumb_url=photo_url)
            self.update.inline_query.answer([result], cache_time=(360 if Settings.production else 0))
        elif self.update_type == UpdateType.button_press:
            self.update.callback_query.answer(text)

    def edit(self, text=None, photo_url=None, reply_markup=None, parse_mode=None, photo_primary=False):
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
        if photo_url and not photo_primary:
            if parse_mode is None or parse_mode.lower() != "html":
                parse_mode = "html"
                text = html.escape(text)
            text = add_photo_to_text(text, photo_url)
        if self.update_type == UpdateType.button_press:
            kwargs = dict(parse_mode=parse_mode,
                          reply_markup=reply_markup)
            if photo_url is not None and photo_primary:
                kwargs = dict(
                    media=InputMediaPhoto(media=photo_url[0], caption=text,
                                          parse_mode=parse_mode),
                    reply_markup=reply_markup,
                )
                if self.update.callback_query.inline_message_id is not None:
                    kwargs["inline_message_id"] = self.update.callback_query.inline_message_id
                else:
                    logger.debug("chat instance %s", self.update.callback_query.chat_instance)
                    kwargs["chat_id"] = self.update.callback_query.message.chat_id
                    kwargs["message_id"] = self.update.callback_query.message.message_id
                try:
                    self.bot.edit_message_media(**kwargs)
                except telegram.error.TelegramError:
                    if parse_mode.lower() != 'html':
                        text = html.escape(text)
                    text = f'<b><a href="{photo_url[0]}">Link to image</a></b>\n\n' + text
                    kwargs["media"] = InputMediaPhoto(media=Settings.no_image, caption=text, parse_mode=parse_mode)
                    self.bot.edit_message_media(**kwargs)
            elif text is not None and not photo_primary:
                self.update.callback_query.edit_message_text(
                    text=text, **kwargs
                )
            elif text is not None and photo_primary:
                self.update.callback_query.edit_message_caption(
                    caption=text, **kwargs
                )
            elif reply_markup is not None:
                logger.debug("updating reply markup to %s", reply_markup)
                self.update.callback_query.edit_message_reply_markup(reply_markup)
            if octobot.Database is not None and self.kbd_id is not None:
                logger.debug("Edit called OK, deleting inline keyboard data for %s", self.kbd_id)
                Database.redis.delete(generate_inline_entry(self.kbd_id))
                self.kbd_id = None
        elif self.update_type in [UpdateType.edited_message, UpdateType.message] and self.edit_tgt is not None:
            if text is not None:
                return self.bot.edit_message_text(chat_id=self.update.message.chat.id, message_id=self.edit_tgt,
                                                  text=text, parse_mode=parse_mode, reply_markup=reply_markup)
            elif reply_markup is not None:
                return self.bot.edit_message_reply_markup(chat_id=self.update.message.chat.id, message_id=self.edit_tgt,
                                                          reply_markup=reply_markup)

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
