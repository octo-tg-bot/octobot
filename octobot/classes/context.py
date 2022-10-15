from uuid import uuid4
from settings import Settings
from octobot.utils import add_photo_to_text
import gettext
import html
import logging
import re
import shlex
import warnings
from functools import wraps
import time

import babel
import telegram
import telegram.ext
from telegram import InputMediaPhoto

import octobot
import octobot.exceptions
from octobot import database

Database = database.Database

logger = logging.getLogger("Context")


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return html.unescape(cleantext)


def pluginfo_kwargs(field_name):
    def decorator(function):
        @wraps(function)
        def call_func(self, *args, **kwargs):
            plugin = self._plugin
            kw = {}
            if plugin != "unknown":
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
    :vartype locale: :class:`babel.Locale`
    :var update_type: DEPRECATED: Type of update
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
    called_command = None
    user: telegram.User
    chat: telegram.Chat
    _update_type = 'unknown'

    def __init__(self, update: telegram.Update, bot: "octobot.OctoBot", message: telegram.Message = None):
        if Context == type(self):
            raise RuntimeError(
                "Calling Context class directly! Please use Context.create_context instead...")
        self.locale_str = "en"
        self.bot = bot
        self.update = update
        self.locale_str = octobot.localization.get_chat_locale(self.update)
        if "_" in self.locale_str:
            loc_sep = "_"
        else:
            loc_sep = "-"
        self.locale = babel.Locale.parse(self.locale_str, sep=loc_sep)
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
        if self.text is None:
            self.text = ''
        self.query = " ".join(self.text.split(" ")[1:])
        try:
            self.args = shlex.split(self.query)
        except ValueError:
            self.args = self.query.split(" ")

    @property
    def update_type(self):
        warnings.warn("Context.update_type is deprecated! Use isinstance on context instead to check update type.",
                      DeprecationWarning, 2)
        return self._update_type

    @pluginfo_kwargs("reply_kwargs")
    def reply(self, text, photo_url=None, reply_to_previous=False, reply_markup=None, parse_mode=None, no_preview=False,
              title=None, to_pm=False, failed=False, editable=True, inline_description=None, photo_primary=False,
              file_url=None):
        """
        Replies to a message/shows a popup in inline keyboard/sends out inline query result

        :param text: Text to send
        :type text: :class:`str`
        :param photo_url: Photo URLs, with best quality descending to worst
        :type photo_url: :class:`list`, optional
        :param file_url: File URL to send, message only
        :type file_url: :class:`list`, optional
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
        if photo_url and not photo_primary:
            if parse_mode is None or parse_mode.lower() != "html":
                parse_mode = "html"
                text = html.escape(text)
            text = add_photo_to_text(text, photo_url)
        if title is None:
            title = self.text[:20]
        if to_pm:
            return MessageContext._reply(text, photo_url, reply_to_previous, reply_markup, parse_mode, no_preview,
                                         title, to_pm, failed, editable, inline_description, photo_primary,
                                         file_url)
        return self._reply(text, photo_url, reply_to_previous, reply_markup, parse_mode, no_preview,
                           title, to_pm, failed, editable, inline_description, photo_primary,
                           file_url)

    def _reply(self, text, photo_url=None, reply_to_previous=False, reply_markup=None, parse_mode=None,
               no_preview=False,
               title=None, to_pm=False, failed=False, editable=True, inline_description=None, photo_primary=False,
               file_url=None):
        raise RuntimeError(f"Override _reply in {type(self)}!")

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
        if photo_url and not photo_primary:
            if parse_mode is None or parse_mode.lower() != "html":
                parse_mode = "html"
                text = html.escape(text)
            text = add_photo_to_text(text, photo_url)
        return self._edit(text, photo_url, reply_markup, parse_mode, photo_primary)

    def _edit(self, text=None, photo_url=None, reply_markup=None, parse_mode=None, photo_primary=False):
        raise RuntimeError(f"Override _edit in {type(self)}!")

    def localize(self, text: str) -> str:
        """
        Localize string according to user-set localization

        :param text: String to translate
        :type text: :class:`str`
        :return: Localized string
        :rtype: :class:`str`
        """
        gt = gettext.translation("messages", localedir="locales", languages=[
                                 self.locale_str], fallback=True)

        return gt.gettext(text)

    def nlocalize(self, singular: str, plural: str, n: int) -> str:
        """
        Localize string according to user-set localization, taking pluralization into account

        :param singular: Singular form of the string to translate
        :type singular: :class:`str`
        :param plural: Plural form of the string to translate
        :type plural: :class:`str`
        :param n: The number in question
        :type n: :class:`int`
        :return: Localized string
        :rtype: :class:`str`
        """
        gt = gettext.translation("messages", localedir="locales", languages=[
                                 self.locale_str], fallback=True)

        return gt.ngettext(singular, plural, n)

    @staticmethod
    def create_context(update, bot, message=None):
        if message is None and update.message is not None:
            message = update.message

        if update.inline_query:
            return InlineQueryContext(update, bot, message)
        elif update.callback_query:
            return CallbackContext(update, bot, message)
        elif message:
            return MessageContext(update, bot, message)
        elif update.edited_message:
            return EditedMessageContext(update, bot, message)
        elif update.chosen_inline_result:
            return ChosenInlineResultContext(update, bot, message)
        else:
            raise octobot.exceptions.UnknownUpdate(
                "Failed to determine update type for update %s", update.to_dict())


class InlineQueryContext(Context):
    """
    Context for inline queries
    """

    def __init__(self, update: telegram.Update, bot: "octobot.OctoBot", message: telegram.Message = None):
        self.text = update.inline_query.query
        self._update_type = octobot.UpdateType.inline_query
        super(InlineQueryContext, self).__init__(update, bot, message)

    def _reply(self, text, photo_url=None, reply_to_previous=False, reply_markup=None, parse_mode=None,
               no_preview=False,
               title=None, to_pm=False, failed=False, editable=True, inline_description=None, photo_primary=False,
               file_url=None):
        inline_content = telegram.InputTextMessageContent(
            text,
            parse_mode=parse_mode,
            disable_web_page_preview=no_preview
        )
        result = telegram.InlineQueryResultArticle(uuid4(),
                                                   title=title,
                                                   description=cleanhtml(text)[
                                                       :500] if inline_description is None else inline_description,
                                                   input_message_content=inline_content,
                                                   reply_markup=reply_markup,
                                                   thumb_url=photo_url)
        self.update.inline_query.answer(
            [result], cache_time=(360 if Settings.production else 0))


class CallbackContext(Context):
    """
    Context for callbacks
    """

    def __init__(self, update: telegram.Update, bot: "octobot.OctoBot", message: telegram.Message = None):
        self.callback_data = update.callback_query.data
        self.text = ''
        if isinstance(self.callback_data, str):
            self.text = update.callback_query.data
        elif isinstance(self.callback_data, telegram.ext.InvalidCallbackData):
            self.callback_data = octobot.InvalidCallback
        logger.debug("text: %s" % self.text)
        self._update_type = octobot.UpdateType.button_press
        super(CallbackContext, self).__init__(update, bot, message)

    def _reply(self, text, photo_url=None, reply_to_previous=False, reply_markup=None, parse_mode=None,
               no_preview=False,
               title=None, to_pm=False, failed=False, editable=True, inline_description=None, photo_primary=False,
               file_url=None):
        self.update.callback_query.answer(text)

    def _edit(self, text=None, photo_url=None, reply_markup=None, parse_mode=None, photo_primary=False):
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
                logger.debug("chat instance %s",
                             self.update.callback_query.chat_instance)
                kwargs["chat_id"] = self.update.callback_query.message.chat_id
                kwargs["message_id"] = self.update.callback_query.message.message_id
            try:
                self.bot.edit_message_media(**kwargs)
            except telegram.error.TelegramError:
                if parse_mode.lower() != 'html':
                    text = html.escape(text)
                text = f'<b><a href="{photo_url[0]}">Link to image</a></b>\n\n' + text
                kwargs["media"] = InputMediaPhoto(
                    media=Settings.no_image, caption=text, parse_mode=parse_mode)
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
        logger.debug("Delete callback data result: %s",
                     self.bot.callback_data_cache.drop_data(self.update.callback_query))


class MessageContext(Context):
    """
    Context for text messages
    """

    def __init__(self, update: telegram.Update, bot: "octobot.OctoBot", message: telegram.Message = None):
        if message.caption is not None:
            self.text = message.caption
        else:
            self.text = message.text
        self._update_type = octobot.UpdateType.message
        is_reply = message is not None
        if octobot.Database.redis is not None and not is_reply:
            octobot.Database.redis.set(
                octobot.utils.generate_edit_id(update.message), 0)
            octobot.Database.redis.expire(
                octobot.utils.generate_edit_id(update.message), 30)
        if message.reply_to_message:
            self.reply_to_message = Context.create_context(
                update, bot, update.message.reply_to_message)
        super(MessageContext, self).__init__(update, bot, message)

    def _reply(self, text, photo_url=None, reply_to_previous=False, reply_markup=None, parse_mode=None,
               no_preview=False,
               title=None, to_pm=False, failed=False, editable=True, inline_description=None, photo_primary=False,
               file_url=None):
        if reply_to_previous and (self.update.message.reply_to_message is not None):
            target_msg: telegram.Message = self.update.message.reply_to_message
        else:
            target_msg: telegram.Message = self.update.message
        kwargs = dict(chat_id=target_msg.chat_id, parse_mode=parse_mode,
                      reply_markup=reply_markup, disable_web_page_preview=no_preview,
                      reply_to_message_id=target_msg.message_id, allow_sending_without_reply=True)
        if to_pm:
            kwargs["chat_id"] = self.user.id
            del kwargs["reply_to_message_id"]
        if photo_url and photo_primary:
            try:
                if "disable_web_page_preview" in kwargs:
                    del kwargs["disable_web_page_preview"]
                message = self.bot.send_photo(
                    caption=text, photo=photo_url[0], **kwargs)
            except telegram.error.TelegramError:
                if parse_mode.lower() != 'html':
                    text = html.escape(text)
                text = f'<b><a href="{photo_url[0]}">Link to image</a></b>\n\n' + text
                message = self.bot.send_photo(
                    caption=text, photo=Settings.no_image, **kwargs)
        elif file_url:
            if "disable_web_page_preview" in kwargs:
                del kwargs["disable_web_page_preview"]
            try:
                message = self.bot.send_document(
                    caption=text, document=file_url, **kwargs)
            except telegram.error.TelegramError:
                text = f'<b>Failed to send file. <a href="{photo_url[0]}">Link to file</a></b>\n\n' + text
                message = self.bot.send_message(text=text, **kwargs)
        else:
            message = self.bot.send_message(text=text, **kwargs)

        if octobot.Database.redis is not None and editable:
            octobot.Database.redis.set(octobot.utils.generate_edit_id(
                self.update.message), message.message_id)
            octobot.Database.redis.expire(
                octobot.utils.generate_edit_id(self.update.message), 30)
        self.edit_tgt = message.message_id
        return message

    def _edit(self, text=None, photo_url=None, reply_markup=None, parse_mode=None, photo_primary=False):
        if self.edit_tgt is not None:
            if text is not None:
                return self.bot.edit_message_text(chat_id=self.update.message.chat.id, message_id=self.edit_tgt,
                                                  text=text, parse_mode=parse_mode, reply_markup=reply_markup)
            elif reply_markup is not None:
                return self.bot.edit_message_reply_markup(chat_id=self.update.message.chat.id, message_id=self.edit_tgt,
                                                          reply_markup=reply_markup)


class EditedMessageContext(MessageContext):
    """
    Context for edited text messages
    """

    def __init__(self, update: telegram.Update, bot: "octobot.OctoBot", message: telegram.Message = None):
        self.update = update
        self.update.message = self.update.edited_message
        if octobot.Database.redis.exists(octobot.utils.generate_edit_id(self.update.message)):
            self.edit_tgt = int(octobot.Database.redis.get(
                octobot.utils.generate_edit_id(self.update.message)))
            if self.edit_tgt == 0:
                logger.debug(
                    "Not handling update %s cause invalid edit target", update.update_id)
                raise octobot.StopHandling
            octobot.Database.redis.delete(
                octobot.utils.generate_edit_id(self.update.message))
            self._update_type = octobot.UpdateType.edited_message
            if update.message.caption is not None:
                self.text = update.message.caption
            else:
                self.text = update.message.text
        else:
            logger.debug(
                "Not handling update %s cause not available in database", update.update_id)
            raise octobot.StopHandling
        logger.debug("edit target = %s", self.edit_tgt)
        # super(EditedMessageContext, self).__init__(update, bot, message)
        Context.__init__(self, update, bot, message)

    def _reply(self, text, photo_url=None, reply_to_previous=False, reply_markup=None, parse_mode=None,
               no_preview=False,
               title=None, to_pm=False, failed=False, editable=True, inline_description=None, photo_primary=False,
               file_url=None):
        return self.edit(text=text, photo_url=photo_url, reply_markup=reply_markup, parse_mode=parse_mode)


class ChosenInlineResultContext(Context):
    """
    Context for chosen inline query result messages
    """

    def __init__(self, update: telegram.Update, bot: "octobot.OctoBot", message: telegram.Message = None):
        self._update_type = octobot.UpdateType.chosen_inline_result
        self.text = update.chosen_inline_result.query
        super(ChosenInlineResultContext, self).__init__(update, bot, message)
