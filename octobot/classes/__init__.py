import html

import telegram

import octobot

class UpdateType:
    inline_query = 0
    button_press = 1
    message = 2


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
            self.text = update.callback_query.query
            self.update_type = UpdateType.button_press
        elif update.message:
            if update.message.caption is not None:
                self.text = update.message.caption
            else:
                self.text = update.message.text
            self.update_type = UpdateType.message
        else:
            raise octobot.UnknownUpdate("Failed to determine update type for update %s", update.to_dict())

    def reply(self, text, photo_url=None, reply_to_previous=True, reply_markup=None, parse_mode=None, no_preview=False, title=None):
        if title is None:
            title = self.text[:20]
        if self.update_type == UpdateType.message:
            if reply_to_previous and (self.update.message.reply_to_message is not None):
                target_msg: telegram.Message = self.update.message.reply_to_message
            else:
                target_msg: telegram.Message = self.update.message
            if photo_url:
                try:
                    target_msg.reply_photo(photo=photo_url,
                                           caption=text,
                                           parse_mode=parse_mode,
                                           reply_markup=reply_markup)
                except telegram.error.BadRequest as e:
                    if e.message.startswith("Wrong file"):
                        if parse_mode is None or parse_mode.lower() != "html":
                            text = html.escape(text)
                            parse_mode = 'html'
                        text = f'<a href="{photo_url}">Photo</a>\n' + text
                        target_msg.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
            else:
                target_msg.reply_text(text=text,
                                      parse_mode=parse_mode,
                                      reply_markup=reply_markup,
                                      disable_web_page_preview=no_preview)

        elif self.update_type == UpdateType.inline_query:
            if photo_url is None:
                result = telegram.InlineQueryResultArticle(self.update.inline_query.query,
                                                           title=title,
                                                           description=text.split("\n")[0],
                                                           input_message_content=telegram.InputTextMessageContent(
                                                               text,
                                                               parse_mode=parse_mode,
                                                               disable_web_page_preview=no_preview
                                                           ),
                                                           reply_markup=reply_markup)
            else:
                result = telegram.InlineQueryResultPhoto(self.update.inline_query.query,
                                                         photo_url=photo_url,
                                                         thumb_url=photo_url,
                                                         title=title,
                                                         description=text.split("\n")[0],
                                                         caption=text,
                                                         parse_mode=parse_mode,
                                                         reply_markup=reply_markup)
            self.update.inline_query.answer([result])
