from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

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


from octobot.classes.context import Context
from octobot.classes.catalog import CatalogKeyPhoto, CatalogKeyArticle, Catalog, CatalogPhoto


@dataclass
class PluginInfo():
    """
    Plugin info class
    """
    name: str
    reply_kwargs: dict = field(default_factory=dict)
    handler_kwargs: dict = field(default_factory=dict)
    after_load: Callable[["octobot.OctoBot"], Any] = None

