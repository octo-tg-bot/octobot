import html
import shlex

import telegram

import octobot
from octobot.classes import UpdateType
from octobot.utils import add_photo_to_text


class Context:
    def __init__(self, update: telegram.Update):
        self.locale = "en"
        self.update = update
        self.user = update.effective_user
        self.chat = update.effective_chat
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
            raise octobot.UnknownUpdate("Failed to determine update type for update %s", update.to_dict())
        self.query = " ".join(self.text.split(" ")[1:])
        self.args = shlex.split(self.query)

    def reply(self, text, photo_url=None, reply_to_previous=False, reply_markup=None, parse_mode=None, no_preview=False,
              title=None):
        if photo_url:
            if parse_mode != "html":
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
                result = telegram.InlineQueryResultArticle(self.update.inline_query.query,
                                                         photo_url=photo_url,
                                                         thumb_url=photo_url,
                                                         title=title,
                                                         description=text.split("\n")[0],
                                                         input_message_content=inline_content)
            self.update.inline_query.answer([result])
        elif self.update_type == UpdateType.button_press:
            self.update.callback_query.answer(text)

    def edit(self, text, photo_url=None, reply_markup=None, parse_mode=None):
        if photo_url:
            if parse_mode != "html":
                parse_mode = "html"
                text = html.escape(text)
            text = add_photo_to_text(text, photo_url)
        self.update.callback_query.edit_message_text(
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
