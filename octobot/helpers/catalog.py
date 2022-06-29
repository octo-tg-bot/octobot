import octobot as ob
from .basehelper import BaseHelper
import telegram
import logging
logger = logging.getLogger("catalog")


class CatalogHelper(BaseHelper):
    def __init__(self, command: str, description: str, title: str = None,
                 hero_image: str = None, example_usage: str = None, preferred_count=50):
        """Initializes CatalogHelper

        Args:
            command (str): command that will display catalog
            description (str): description in settings
            title (str): title in inline query suggestion. Defaults to command.
            hero_image (str): image in inline query suggestion. Defaults to None.
            example_usage (str): example usage in inline query suggestion. Defaults to None.
            preferred_count (int, optional): how much things CatalogHelper should ask from function. Defaults to 50 when inline, and (always) 1 in case of message.
        """
        self.command = command
        self.description = description
        self.title = title or command
        self.hero_image = hero_image
        self.example_usage = example_usage
        self.preferred_count = preferred_count

    @property
    def filters(self):
        suggestion = ob.misc.Suggestion(
            self.hero_image, self.title, self.example_usage)
        command_filter = ob.filters.CommandFilter(
            self.command, self.description, self.example_usage, required_args=1, suggestion=suggestion)
        command_filter.insert_func(self.command_handler)
        return [command_filter]

    async def change_page(self, bot, context, offset, query):
        res: ob.catalogs.CatalogResult = await self.function(bot, context, self[offset], query)
        res.query = query
        nav_markup = self.create_nav(res)
        kbd = res[0].reply_markup.inline_keyboard + [nav_markup]
        res[0].reply_markup = telegram.InlineKeyboardMarkup(
            kbd
        )
        await context.edit(**res[0].message)

    def create_nav(self, res: ob.catalogs.CatalogResult):
        logger.debug("offsets: %s, %s", res.previous_offset, res.next_offset)
        if res.previous_offset is None:
            prev_command = ob.EmptyCallback
        else:
            prev_command = ob.Callback(
                self.change_page, res.previous_offset, res.query)
        if res.next_offset is None:
            next_command = ob.EmptyCallback
        else:
            next_command = ob.Callback(
                self.change_page, res.next_offset, res.query)
        return [telegram.InlineKeyboardButton("⬅️", callback_data=prev_command),
                telegram.InlineKeyboardButton(
                    f"{res.current_index}/{res.total or '?'}", callback_data=ob.EmptyCallback),
                telegram.InlineKeyboardButton("➡️", callback_data=next_command)]

    async def command_handler(self, bot, context):
        res: ob.catalogs.CatalogResult = await self.function(bot, context, self[0], context.query)
        res.query = context.query
        nav_markup = self.create_nav(res)
        kbd = res[0].reply_markup.inline_keyboard + [nav_markup]
        res[0].reply_markup = telegram.InlineKeyboardMarkup(
            kbd
        )
        await context.reply(**res[0].message)

    def __getitem__(self, key):
        """A little hack to make life easier"""
        if not isinstance(key, slice):
            return slice(key, key+1)
        return slice
