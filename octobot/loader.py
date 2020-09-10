import base64
import os
from enum import Enum
from glob import glob
import importlib

import telegram

import octobot.exceptions
import octobot.handlers
import logging

from octobot import PluginInfo
from octobot.utils import path_to_module
from settings import Settings

logger = logging.getLogger("Loader")


class PluginStates(Enum):
    loaded = 0
    unknown = 1
    error = 2
    notfound = 3
    skipped = 4


class OctoBot(telegram.Bot):
    """
    Module loader class. Inherited from telegram.Bot

    :param load_list: List of plugins to load in module syntax
    :type list:
    :param \*args: Arguments to pass to telegram.Bot class
    :param \*\*kwargs: Keyword arguments to pass to telegram.Bot class
    """
    plugins = {}
    handlers = {}

    def __init__(self, load_list, *args, **kwargs):
        dry_run = os.environ.get("DRY_RUN", False)
        if not dry_run:
            super(OctoBot, self).__init__(*args, **kwargs)
            self.me = self.getMe()

        for plugin in glob("base_plugins/*.py"):
            logger.info("Loading base plugin %s", plugin)
            self.load_plugin(path_to_module(plugin))
        if len(load_list) > 0:
            load_list_actual = []
            for plugin in load_list:
                load_list_actual.append(path_to_module(plugin))
            self.load_plugins({"exclude": [], "load_order": load_list_actual})
        else:
            plugins = self.discover_plugins()
            self.load_plugins(plugins)

    @staticmethod
    def discover_plugins():
        """
        Search for plugins

        :return: Load dictionary for load_plugins. Consists of "exclude" and "load_order" keys
        :rtype: dict
        """
        modlist = []
        for plugin in glob('plugins/*.py'):
            plugin = path_to_module(plugin)
            modlist.append(plugin)
        load_list = dict(exclude=Settings.exclude_plugins, load_order=modlist)

        return load_list

    def update_handlers(self):
        """
        Updates handlers from self.plugins. Usually gets called after :meth:`load_plugins` or :meth:`load_plugin` (if `single_load=True`)
        """
        self.handlers = {}
        for plugin in self.plugins.values():
            module = plugin["module"]
            for var_name in dir(module):
                var = getattr(module, var_name)
                if isinstance(var, octobot.handlers.BaseHandler):
                    var.plugin = plugin
                    if var.priority not in self.handlers:
                        self.handlers[var.priority] = []
                    if type(var).__name__ in plugin["plugin_info"].handler_kwargs:
                        for k, v in plugin["plugin_info"].handler_kwargs[type(var).__name__].items():
                            setattr(var, k, v)
                    self.handlers[var.priority].append(var)
        logger.info("Handlers update complete, priority levels: %s", self.handlers.keys())
        logger.debug("Running post-load functions...")
        for plugin in self.plugins.values():
            func = plugin["plugin_info"].after_load
            if func is not None:
                func(self)

    def load_plugin(self, plugin: str, single_load=False):
        """
        Loads plugin

        :param plugin: Plugin name in module format (ex. `plugins.test`)
        :type plugin: str
        :param single_load: If plugin is loaded not together with other plugins (e.g. manually loaded from other plugin). Defaults to False
        :type single_load: bool,optional
        """
        self.plugins[plugin] = dict(name=plugin, state=PluginStates.unknown, module=None,
                                    plugin_info=PluginInfo(name=plugin))
        if plugin in Settings.exclude_plugins:
            self.plugins[plugin]["state"] = PluginStates.skipped
            return
        try:
            plugin_module = importlib.import_module(plugin)
        except ModuleNotFoundError:
            self.plugins[plugin]["state"] = PluginStates.notfound
            logger.error("Plugin %s is defined in load_order, but cannot be found. Please check your load_list.json",
                         plugin)
        except octobot.DontLoadPlugin as e:
            self.plugins[plugin]["state"] = PluginStates.skipped
            self.plugins[plugin]["exception"] = str(e)
        except Exception as e:
            logger.error("Failed to load plugin %s", exc_info=True)
            self.plugins[plugin]["state"] = PluginStates.error
            self.plugins[plugin]["exception"] = str(e)
        else:
            self.plugins[plugin]["state"] = PluginStates.loaded
            self.plugins[plugin]["module"] = plugin_module
            for variable in dir(plugin_module):
                variable = getattr(plugin_module, variable)
                if isinstance(variable, PluginInfo):
                    self.plugins[plugin]["plugin_info"] = variable
                    break
            logger.info("Loaded plugin %s", plugin)
        if single_load:
            self.update_handlers()
        return

    def load_plugins(self, load_list: dict):
        """
        Loads plugins using dict generated by :meth:`discover_plugins()`

        :param load_list: Load list. Usually generated by :meth:`discover_plugins()`
        """
        for plugin in load_list["load_order"]:
            self.load_plugin(plugin)
        self.update_handlers()
        return

    def handle_update(self, bot, update):
        logger.debug("handling update %s", update.to_dict())
        try:
            ctx = octobot.Context(update, bot)
        except octobot.exceptions.UnknownUpdate:
            unknown_thing = "unknown, update dict: %s" % update.to_dict()
            for var_name, var in vars(update).items():
                if var is not None and not (var_name.startswith("effective") or var_name.startswith("_") or var_name.startswith("update")):
                    unknown_thing = var_name
            logger.warning("Failed to determine update type: %s", unknown_thing)
            return
        except octobot.exceptions.StopHandling:
            return
        for priority in sorted(self.handlers.keys()):
            handlers = self.handlers[priority]
            logger.debug(f"handling priority level {priority}")
            try:
                for handler in handlers:
                    try:
                        ctx._plugin = handler.plugin
                        handler.handle_update(bot, ctx)
                    except octobot.exceptions.StopHandling as e:
                        raise e
                    except Exception as e:
                        logger.error("Handler threw an exception!", exc_info=True)
            except octobot.exceptions.StopHandling:
                break

    def generate_startlink(self, command):
        command = f"b64-{base64.urlsafe_b64encode(command.encode()).decode()}"
        return f"https://t.me/{self.me.username}?start={command}"

