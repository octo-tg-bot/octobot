import html

import octobot
from octobot.exceptions import CatalogCantGoDeeper, CatalogNotFound, CatalogCantGoBackwards, handle_exception
from octobot.classes.context import Context
from octobot.handlers import CommandHandler
import re
import telegram

from octobot.utils import add_photo_to_text
from settings import Settings

BUTTON_REGEX = re.compile(r"(\w*):(.*(?<!\\)):(.*)$")
BUTTON_LEFT = "◀️"
BUTTON_RIGHT = "▶️"


def create_buttonstring(command, query, next_offset):
    if isinstance(command, list):
        command = command[0]
    query = query.replace(":", r"\:")
    return f"{command}:{query}:{next_offset}"


def create_inline_buttons(command, query, current_index, max_results, previous_offset, next_offset):
    return [
        telegram.InlineKeyboardButton(text=BUTTON_LEFT,
                                      callback_data=create_buttonstring(command, query, previous_offset)),
        telegram.InlineKeyboardButton(text=f"{current_index}/{max_results}", callback_data="nothing:"),
        telegram.InlineKeyboardButton(text=BUTTON_RIGHT,
                                      callback_data=create_buttonstring(command, query, next_offset))
    ]


class CatalogHandler(CommandHandler):
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

    def __init__(self, *args, **kwargs):
        self.query_required = kwargs.pop("query_required", True)
        super(CatalogHandler, self).__init__(*args, **kwargs)

    def handle_page(self, bot, context: Context):
        _, query, offset = BUTTON_REGEX.match(context.text).groups()
        query = query.replace(r"\:", ":")
        offset = offset
        try:
            res: octobot.Catalog = self.function(query, offset, 1, bot, context)
        except CatalogCantGoDeeper:
            return context.reply(context.localize("Can't go forward anymore"))
        except CatalogCantGoBackwards:
            return context.reply(context.localize("Can't go backwards anymore"))
        if res is None:
            return
        reply_markup = telegram.InlineKeyboardMarkup(res[0].reply_markup.inline_keyboard.copy())
        reply_markup.inline_keyboard.append(
            create_inline_buttons(self.command, query, res.current_index, res.max_count, res.previous_offset,
                                  res.next_offset))
        reply_markup.inline_keyboard.append(self.create_current_query_button(query, context))
        context.edit(res[0].text, parse_mode=res[0].parse_mode, photo_url=res[0].photo_msgmode,
                     reply_markup=reply_markup, photo_primary=res.photo_primary)

    def handle_command(self, bot, context: Context):
        query = context.query
        res: octobot.Catalog = self.function(query, 0, 1, bot, context)
        reply_markup = telegram.InlineKeyboardMarkup(res[0].reply_markup.inline_keyboard.copy())
        reply_markup.inline_keyboard.append(
            create_inline_buttons(self.command, query, res.current_index, res.max_count, res.previous_offset,
                                  res.next_offset))
        reply_markup.inline_keyboard.append(self.create_current_query_button(query, context))

        context.reply(res[0].text, parse_mode=res[0].parse_mode, photo_url=res[0].photo_msgmode,
                      reply_to_previous=False,
                      reply_markup=reply_markup, photo_primary=res.photo_primary)

    def handle_inline(self, bot, context: Context):
        query = context.query
        if context.update.inline_query.offset != "":
            offset = int(context.update.inline_query.offset)
        else:
            offset = 0
        try:
            res: octobot.Catalog = self.function(query, offset, 50, bot, context)
        except CatalogCantGoDeeper:
            return
        if res is None:
            return
        inline_res = []
        for item in res:
            if item.reply_markup is None:
                item.reply_markup = telegram.InlineKeyboardMarkup()
            item.reply_markup.inline_keyboard.append(self.create_current_query_button(query, context))
            if item.photo is not None:
                if item.parse_mode is None or item.parse_mode.lower() != "html":
                    item.parse_mode = 'html'
                    item.text = html.escape(item.text)
                text = add_photo_to_text(item.text, item.photo)
                res_kwargs = dict(id=item.item_id,
                                  photo_url=item.photo[0].url,
                                  photo_width=item.photo[0].width,
                                  photo_height=item.photo[0].height,
                                  thumb_url=item.photo[-1].url,
                                  title=item.title,
                                  description=item.description,
                                  reply_markup=item.reply_markup
                                  )
                if res.photo_primary:
                    res_kwargs['caption'] = text
                    res_kwargs['parse_mode'] = item.parse_mode
                else:
                    res_kwargs['input_message_content'] = telegram.InputTextMessageContent(
                        text,
                        parse_mode=item.parse_mode
                    )
                if isinstance(item, octobot.CatalogKeyPhoto):
                    inline_res.append(telegram.InlineQueryResultPhoto(**res_kwargs))
                else:
                    inline_res.append(telegram.InlineQueryResultArticle(**res_kwargs))
            else:
                inline_res.append(telegram.InlineQueryResultArticle(
                    item.item_id,
                    title=item.title,
                    description=item.description,
                    input_message_content=telegram.InputTextMessageContent(
                        item.text,
                        parse_mode=item.parse_mode
                    )
                ))
        context.update.inline_query.answer(inline_res, cache_time=(360 if Settings.production else 0),
                                           next_offset=res.next_offset)

    def handle_update(self, bot, context):
        try:
            chk_cmd = self.check_command(bot, context)
            if chk_cmd:
                if self.plugin.state == octobot.PluginStates.disabled:
                    context.reply(
                        context.localize("Sorry, this command is unavailable. Please contact the bot administrator."))
                    return
                if (context.query == "" and self.query_required) and \
                        context.update_type != octobot.UpdateType.button_press and chk_cmd:
                    return context.reply(context.localize("This command requires query. Specify what you want to find"))
                elif context.update_type in [octobot.UpdateType.message,
                                             octobot.UpdateType.edited_message] and chk_cmd:
                    self.handle_command(bot, context)
                elif context.update_type == octobot.UpdateType.inline_query and chk_cmd:
                    self.handle_inline(bot, context)
            elif context.update_type == octobot.UpdateType.button_press and context.text.split(":")[0] == self.command[
                0]:
                self.handle_page(bot, context)
        except CatalogNotFound:
            context.reply(context.localize("Nothing found!"))
        except Exception as e:
            handle_exception(bot, context, e)

    def create_current_query_button(self, query, ctx):
        return [telegram.InlineKeyboardButton(switch_inline_query_current_chat=f"{self.command[0]} {query}", text=ctx.localize("➡️Search using inline mode"))]
