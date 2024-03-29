import base64
import os
import sys
import threading
from glob import glob
import importlib

import telegram
import telegram.ext
import telegram.error

import octobot.exceptions
import octobot.handlers
import logging

from octobot import PluginInfo, handle_exception, PluginStates
from octobot.utils import path_to_module, thread_local
from settings import Settings

logger = logging.getLogger("Loader")
TEST_RUNNING = "pytest" in sys.modules


class OctoBot(telegram.ext.ExtBot):
    """
    Module loader class. Inherited from telegram.ext.ExtBot

    :param load_list: List of plugins to load in module syntax
    :type list:
    :param \*args: Arguments to pass to telegram.ext.ExtBot class
    :param \*\*kwargs: Keyword arguments to pass to telegram.ext.ExtBot class
    """
    plugins = {}
    handlers = {}
    error_handlers = []
    test_running = TEST_RUNNING

    def __init__(self, load_list, *args, **kwargs):
        dry_run = os.environ.get("DRY_RUN", False)
        if not (dry_run or TEST_RUNNING):
            logger.info("Initializing PTB")
            super(OctoBot, self).__init__(
                arbitrary_callback_data=True, *args, **kwargs)
            self.me = self.getMe()
        if TEST_RUNNING:
            self.me = telegram.User(
                is_bot=True, username="test_bot", id=4, first_name="Unittest")
        for plugin in glob("base_plugins/*.py"):
            logger.info("Loading base plugin %s", plugin)
            self.load_plugin(path_to_module(plugin))
        if len(load_list) > 0:
            logger.info("LoadList: %s", load_list)
            load_list_actual = []
            for plugin in load_list:
                load_list_actual.append(path_to_module(plugin))
            self.load_plugins({"exclude": [], "load_order": load_list_actual})
        else:
            logger.info("LoadList not specified, loading all")
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
        logger.info("Handlers update complete, priority levels: %s",
                    self.handlers.keys())
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
            if octobot.exceptions.IS_DEBUG:
                raise e
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

    def handle_update(self, bot, update: telegram.Update):
        logger.debug("handling update %s", update.to_dict())
        thread_local.current_context = None
        try:
            ctx = octobot.Context.create_context(update, bot)
            thread_local.current_context = ctx
        except octobot.exceptions.UnknownUpdate:
            unknown_thing = "unknown, update dict: %s" % update.to_dict()
            for var_name, var in vars(update).items():
                if var is not None and not (var_name.startswith("effective") or var_name.startswith("_") or var_name.startswith("update")):
                    unknown_thing = var_name
            logger.warning("Failed to determine update type: %s",
                           unknown_thing, exc_info=True)
            return
        except octobot.exceptions.StopHandling:
            return
        disabled_plugins = []
        if octobot.Database.redis is not None and update.effective_message is not None and update.effective_chat.type == "supergroup":
            disabled_plugins = octobot.Database.redis.smembers(
                f"plugins_disabled{update.effective_chat.id}")
        if isinstance(ctx, octobot.CallbackContext) and isinstance(ctx.callback_data, octobot.Callback):
            return ctx.callback_data.execute(bot, ctx)
        for priority in sorted(self.handlers.keys()):
            handlers = self.handlers[priority]
            logger.debug(f"handling priority level {priority}")
            try:
                for handler in handlers:
                    if handler.plugin.module.__name__.encode() in disabled_plugins or handler.plugin.state == PluginStates.disabled:
                        continue
                    try:
                        ctx._plugin = handler.plugin
                        ctx._handler = handler
                        handler.handle_update(bot, ctx)
                    except octobot.exceptions.Halt as e:
                        raise e
                    except octobot.exceptions.StopHandling as e:
                        raise e
                    except octobot.exceptions.PassExceptionToDebugger as e:
                        raise e
                    except telegram.error.TimedOut:
                        pass
                    except Exception as e:
                        logger.error(
                            "Handler threw an exception!", exc_info=True)
                        handle_exception(self, ctx, e, notify=False)
            except octobot.exceptions.StopHandling:
                break
            except octobot.exceptions.PassExceptionToDebugger as e:
                raise e.exception
        # if update.inline_query and not ctx.replied:
        #     update.inline_query.answer([], switch_pm_text=ctx.localize("Click here for command list"), switch_pm_parameter="help")

    def generate_startlink(self, command):
        command = f"b64-{base64.urlsafe_b64encode(command.encode()).decode()}"
        return f"https://t.me/{self.me.username}?start={command}"

    def stop(self):
        raise octobot.exceptions.Halt
