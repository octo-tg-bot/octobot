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
    chosen_inline_result = 4
    """Chosen inline result"""


from octobot.classes.context import Context
from octobot.enums import PluginStates
from octobot.classes.catalog import CatalogKeyPhoto, CatalogKeyArticle, Catalog, CatalogPhoto


@dataclass
class PluginInfo():
    """
    Plugin info class

    :param name: Name of plugin that will show up in /help. The only required argument
    :type name: str
    :param reply_kwargs: Keyword arguments that will be passed to all context.reply calls inside plugin
    :type reply_kwargs: dict, optional
    :param handler_kwargs: Keyword arguments that will be passed to all handlers inside the plugin
    :type handler_kwars: dict, optional
    :param after_load: Function that will be called after bot finishes loading all plugins
    :type after_load: callable, optional
    :param state: Plugin state. Will be overwritten by loader if set to default (PluginStates.unknown). Will also be overwritten if set to default and logger.warning method was used
    :type state: octobot.enums.PluginState, optional
    :param state_description: Description for current plugin state
    :type state_description: str, optional
    :param module: Plugin module. Dont pass anything to that argument, used by loader and handlers
    :var logger: Logger, generated by PluginInfo. Not an argument, a variable
    :type logger: `logging.Logger`
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
