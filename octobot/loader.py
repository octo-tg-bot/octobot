import base64
import os
from glob import glob
import importlib

import telegram

import octobot.exceptions
import octobot.handlers
import logging

from octobot import PluginInfo, handle_exception, PluginStates
from octobot.utils import path_to_module
from settings import Settings

logger = logging.getLogger("Loader")


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
    error_handlers = []

    def __init__(self, load_list, *args, **kwargs):
        dry_run = os.environ.get("DRY_RUN", False)
        if not dry_run:
            logger.info("Initializing PTB")
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
                if isinstance(var, octobot.handlers.ExceptionHandler):
                    self.error_handlers.append(var)
                if isinstance(var, octobot.handlers.BaseHandler):
                    var.plugin = plugin
                    if var.priority not in self.handlers:
                        self.handlers[var.priority] = []
                    if type(var).__name__ in plugin.handler_kwargs:
                        for k, v in plugin.handler_kwargs[type(var).__name__].items():
                            setattr(var, k, v)
                    self.handlers[var.priority].append(var)
        logger.info("Handlers update complete, priority levels: %s", self.handlers.keys())
        logger.debug("Running post-load functions...")
        for plugin in self.plugins.values():
            func = plugin.after_load
            if func is not None:
                func(self)

    def load_plugin(self, plugin_name: str, single_load=False):
        """
        Loads plugin

        :param plugin_name: Plugin name in module format (ex. `plugins.test`)
        :type plugin_name: str
        :param single_load: If plugin is loaded not together with other plugins (e.g. manually loaded from other plugin). Defaults to False
        :type single_load: bool,optional
        """
        if plugin_name in self.plugins:
            old_plugin = self.plugins[plugin_name]
        else:
            old_plugin = None
        # self.plugins[plugin] = dict(name=plugin, state=PluginStates.unknown, module=None,
        #                             plugin_info=PluginInfo(name=plugin), last_warning=None)
        plugin = PluginInfo(name=plugin_name)
        self.plugins[plugin_name] = plugin

        if plugin_name in Settings.exclude_plugins:
            plugin.state = PluginStates.skipped
            return "skipped"
        try:
            if old_plugin and old_plugin.module:
                plugin_module = importlib.reload(old_plugin.module)
            else:
                plugin_module = importlib.import_module(plugin_name)
        except octobot.DontLoadPlugin as e:
            plugin.state = PluginStates.skipped
            plugin.state_description = str(e)
            res = "skipped"
        except Exception as e:
            logger.error("Failed to load plugin %s", exc_info=True)
            plugin.state = PluginStates.error
            plugin.state_description = str(e)
            res = f"crashed, {e}"
            if old_plugin and old_plugin.module:
                res = f"crashed ({e}), old version restored"
                self.plugins[plugin_name] = old_plugin
        else:
            plugin.state = PluginStates.loaded
            plugin.module = plugin_module
            for variable in dir(plugin_module):
                variable = getattr(plugin_module, variable)
                if isinstance(variable, PluginInfo):
                    variable.module = plugin_module
                    if variable.state == PluginStates.unknown:
                        variable.state = PluginStates.loaded
                    self.plugins[plugin_name] = variable
                    lw = variable.last_warning
                    if lw and variable.state != PluginStates.disabled:
                        variable.state = PluginStates.warning
                        variable.state_description = lw
                    break
            logger.info("Loaded plugin %s", plugin_name)
            res = "loaded"
        if single_load:
            self.update_handlers()
        return res

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
                        ctx._handler = handler
                        handler.handle_update(bot, ctx)
                    except octobot.exceptions.Halt as e:
                        raise e
                    except octobot.exceptions.StopHandling as e:
                        raise e
                    except Exception as e:
                        logger.error("Handler threw an exception!", exc_info=True)
                        handle_exception(self, ctx, e, notify=False)
            except octobot.exceptions.StopHandling:
                break

    def generate_startlink(self, command):
        command = f"b64-{base64.urlsafe_b64encode(command.encode()).decode()}"
        return f"https://t.me/{self.me.username}?start={command}"

    def stop(self):
        raise octobot.exceptions.Halt
