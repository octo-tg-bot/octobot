import html
import shlex
import gettext

import telegram

import octobot
import octobot.exceptions
from octobot.classes import UpdateType
from octobot.utils import add_photo_to_text
from octobot.database import Database

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

    def __init__(self, update: telegram.Update):
        self.locale = "en"
        self.update = update
        self.user = update.effective_user
        if self.user is not None:
            self.user_db = Database[self.user.id]
        else:
            self.user_db = None
        self.chat = update.effective_chat
        if self.chat is not None:
            self.chat_db = Database[self.chat.id]
        else:
            self.chat_db = None
        if update.inline_query:
            self.text = update.inline_query.query
            self.update_type = UpdateType.inline_query
        elif update.callback_query:
            self.text = update.callback_query.data
            self.update_type = UpdateType.button_press
        elif update.message:
            if update.message.caption is not None:
                self.text = update.message.caption
            else:
                self.text = update.message.text
            self.update_type = UpdateType.message
        else:
            raise octobot.exceptions.UnknownUpdate("Failed to determine update type for update %s", update.to_dict())
        self.query = " ".join(self.text.split(" ")[1:])
        self.args = shlex.split(self.query)

    def reply(self, text, photo_url=None, reply_to_previous=False, reply_markup=None, parse_mode=None, no_preview=False,
              title=None):
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
        """
        if photo_url:
            if parse_mode is None or parse_mode.lower() != "html":
                parse_mode = "html"
                text = html.escape(text)
            text = add_photo_to_text(text, photo_url)
        if title is None:
            title = self.text[:20]
        if self.update_type == UpdateType.message:
            if reply_to_previous and (self.update.message.reply_to_message is not None):
                target_msg: telegram.Message = self.update.message.reply_to_message
            else:
                target_msg: telegram.Message = self.update.message

            target_msg.reply_text(text=text,
                                  parse_mode=parse_mode,
                                  reply_markup=reply_markup,
                                  disable_web_page_preview=no_preview)

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
            self.update.inline_query.answer([result])
        elif self.update_type == UpdateType.button_press:
            self.update.callback_query.answer(text)

    def edit(self, text, photo_url=None, reply_markup=None, parse_mode=None):
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
        if photo_url:
            if parse_mode.lower() != "html":
                parse_mode = "html"
                text = html.escape(text)
            text = add_photo_to_text(text, photo_url)
        self.update.callback_query.edit_message_text(
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )

    def localize(self, text: str) -> str:
        """
        Localize string according to user-set localization

        :param text: String to translate
        :type text: :class:`str`
        :return: Localized string
        :rtype: :class:`str`
        """
        if self.update.effective_chat.id is not None:
            chatid = self.update.effective_chat.id
        else:
            chatid = self.update.effective_user.id
        chat_locale = octobot.localization.get_chat_locale(chatid)
        gt = gettext.translation("messages", localedir="locales", languages=[chat_locale], fallback=True)
        gt.install()

        return gt.gettext(text)
