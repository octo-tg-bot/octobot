from octobot.classes.callback import Callback, EmptyCallback, InvalidCallback, PopupCallback
from octobot.classes.catalog import CatalogKeyPhoto, CatalogKeyArticle, Catalog, CatalogPhoto
from octobot.classes.context import Context, CallbackContext, MessageContext, ChosenInlineResultContext, \
    EditedMessageContext, InlineQueryContext
from enum import Enum
from octobot.classes.plugininfo import PluginInfo


class UpdateType(Enum):
    """Update types"""
    inline_query = 0
    """Inline query"""
    button_press = 1
    """Inline keyboard button press"""
    message = 2
    """Message"""
    edited_message = 3
    """Edited message"""
    chosen_inline_result = 4
    """Chosen inline result"""
