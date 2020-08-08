import html

import octobot
from octobot.exceptions import CatalogCantGoDeeper, CatalogNotFound
from octobot.classes.context import Context
from octobot.handlers import BaseHandler
import re
import telegram

from octobot.utils import add_photo_to_text

BUTTON_REGEX = re.compile(r"(\w*):(.*(?<!\\)):(.*)$")
BUTTON_LEFT = "◀️"
BUTTON_RIGHT = "▶️"


def create_buttonstring(command, query, next_offset):
    if isinstance(command, list):
        command = command[0]
    query = query.replace(":", r"\:")
    return f"{command}:{query}:{next_offset}"


def create_inline_buttons(command, query, current_offset, max_results):
    return telegram.InlineKeyboardMarkup([
        [
            telegram.InlineKeyboardButton(text=BUTTON_LEFT,
                                          callback_data=create_buttonstring(command, query, current_offset - 1)),
            telegram.InlineKeyboardButton(text=f"{current_offset + 1}/{max_results}", callback_data="nothing:"),
            telegram.InlineKeyboardButton(text=BUTTON_RIGHT,
                                          callback_data=create_buttonstring(command, query, current_offset + 1))
        ]
    ])


class CatalogHandler(BaseHandler):
    """
    Catalog handler. Handles catalogs, surprisingly enough.

    .. note:: Prefix will not be checked in case of inline queries

    :param command: Command to handle
    :type command: list,str
    :param description: Command description
    :type description: str
    :param prefix: Command prefix, defaults to `/`
    :type prefix: str,optional
    """
    def __init__(self, command, description="No description provided", prefix="/", *args, **kwargs):
        super(CatalogHandler, self).__init__(*args, **kwargs)
        self.prefix = prefix
        if isinstance(command, str):
            command = [command]
        self.command = command
        self.description = description

    def handle_page(self, bot, context: Context):
        _, query, offset = BUTTON_REGEX.match(context.text).groups()
        query = query.replace(r"\:", ":")
        offset = int(offset)
        if offset < 0:
            return context.reply("Can't go backwards anymore")
        try:
            res: octobot.Catalog = self.function(query, offset, 1, bot, context)
        except CatalogCantGoDeeper:
            return context.reply("Can't go forward anymore")
        reply_markup = create_inline_buttons(self.command, query, offset, res.total_count)
        context.edit(res[0].text, parse_mode=res[0].parse_mode, photo_url=res[0].photo[0].url,
                     reply_markup=reply_markup)

    def handle_command(self, bot, context: Context):
        query = context.query
        res: octobot.Catalog = self.function(query, 0, 1, bot, context)
        reply_markup = create_inline_buttons(self.command, query, 0, res.total_count)
        context.reply(res[0].text, parse_mode=res[0].parse_mode, photo_url=res[0].photo[0].url, reply_to_previous=False,
                      reply_markup=reply_markup)

    def handle_inline(self, bot, context: Context):
        query = context.query
        if context.update.inline_query.offset != "":
            offset = int(context.update.inline_query.offset)
        else:
            offset = 0
        res: octobot.Catalog = self.function(query, offset, 50, bot, context)
        inline_res = []
        for item in res:
            if item.title is not None:
                title = item.title
            else:
                title = item.text.split("\n")[0][:20]
            if item.photo is not None:
                if item.parse_mode != "html":
                    item.parse_mode = 'html'
                    item.text = html.escape(item.text)
                text = add_photo_to_text(item.text, item.photo)
                res_kwargs = dict(id=item.item_id,
                                  photo_url=item.photo[0].url,
                                  photo_width=item.photo[0].width,
                                  photo_height=item.photo[0].height,
                                  thumb_url=item.photo[-1].url,
                                  title=title,
                                  description=item.text.split("\n")[0],
                                  input_message_content=telegram.InputTextMessageContent(
                                      text,
                                      parse_mode=item.parse_mode
                                  )
                                  )
                if isinstance(item, octobot.CatalogKeyPhoto):
                    inline_res.append(telegram.InlineQueryResultPhoto(**res_kwargs))
                else:
                    inline_res.append(telegram.InlineQueryResultArticle(**res_kwargs))
            else:
                inline_res.append(telegram.InlineQueryResultArticle(
                    item.item_id,
                    title=title,
                    description=item.text.split("\n")[0],
                    input_message_content=telegram.InputTextMessageContent(
                        item.text,
                        parse_mode=item.parse_mode
                    )
                ))
        if len(inline_res) < 50:
            next_offset = None
        else:
            next_offset = offset + 50
        context.update.inline_query.answer(inline_res, cache_time=0, next_offset=next_offset)

    def handle_update(self, bot, context):
        if context.update_type == octobot.UpdateType.button_press and context.text.split(":")[0] == self.command[0]:
            self.handle_page(bot, context)
        if context.update_type in [octobot.UpdateType.message, octobot.UpdateType.inline_query]:
            check_command = octobot.CommandHandler.check_command(self.prefix, self.command, bot, context)
            check_command_inline = octobot.CommandHandler.check_command("", self.command, bot, context)
            if context.update_type == octobot.UpdateType.message and check_command:
                self.handle_command(bot, context)
            elif context.update_type == octobot.UpdateType.inline_query and check_command_inline:
                self.handle_inline(bot, context)
