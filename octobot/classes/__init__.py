import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Dict


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
from octobot.enums import PluginStates
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
    logger: logging.Logger = field(init=False)
    state: PluginStates = PluginStates.unknown
    state_description: str = "state_description was not overwritten"
    last_warning: str = None
    module = None

    def __post_init__(self):
        self.logger = logging.getLogger(self.name)

        def warning(msg, *args, **kwargs):
            self.last_warning = str(msg) % args
            logging.Logger.warning(self.logger, msg, *args, **kwargs)

        self.logger.warning = warning

    def __getitem__(self, item):
        return getattr(self, item)
