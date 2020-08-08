from enum import Enum
class UpdateType(Enum):
    """Update types"""
    inline_query = 0
    """Inline query"""
    button_press = 1
    """Inline keyboard button press"""
    message = 2
    """Message"""


from octobot.classes.context import Context
from octobot.classes.catalog import CatalogKeyPhoto, CatalogKeyArticle, Catalog, CatalogPhoto
from octobot import CatalogCantGoDeeper
