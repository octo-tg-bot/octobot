import base64
import os
import sys
from glob import glob
import importlib

import telegram
import telegram.ext
import telegram.error

import octobot.exceptions
import octobot.handlers
import logging

from octobot import settings, database
from octobot import PluginInfo, PluginStates, MessageContext
from octobot.exceptions import handle_exception
from octobot.utils import path_to_module, current_context

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

    def __init__(self, *args, **kwargs):
        dry_run = os.environ.get("DRY_RUN", False)
        kwargs["token"] = settings.telegram_token
        kwargs["base_url"] = settings.telegram_base_url
        kwargs["base_file_url"] = settings.telegram_base_file_url
        if not (dry_run or TEST_RUNNING):
            logger.info("Initializing PTB")
            super(OctoBot, self).__init__(
                arbitrary_callback_data=True, *args, **kwargs)
        if TEST_RUNNING:
            self.me = telegram.User(
                is_bot=True, username="test_bot", id=4, first_name="Unittest")

    @classmethod
    async def create(cls, load_list, settings, *args, **kwargs):
        self = cls(*args, **kwargs)
        self.me = await self.getMe()
        for plugin in glob("base_plugins/*.py"):
            logger.info("Loading base plugin %s", plugin)
            await self.load_plugin(path_to_module(plugin))
        if len(load_list) > 0:
            logger.info("LoadList: %s", load_list)
            load_list_actual = []
            for plugin in load_list:
                load_list_actual.append(path_to_module(plugin))
            await self.load_plugins({"exclude": [], "load_order": load_list_actual})
        else:
            logger.info("LoadList not specified, loading all")
            plugins = self.discover_plugins()
            await self.load_plugins(plugins)
        return self

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
        load_list = dict(exclude=settings.exclude_plugins,
                         load_order=modlist)

        return load_list

    async def update_handlers(self):
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

    async def load_plugin(self, plugin_name: str, single_load=False):
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

        if plugin_name in settings.exclude_plugins:
            plugin.state = PluginStates.skipped
            return "skipped"
        try:
            if old_plugin and old_plugin.module:
                plugin_module = importlib.reload(old_plugin.module)
            else:
                plugin_module = importlib.import_module(plugin_name)
        except octobot.exceptions.DontLoadPlugin as e:
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
            await self.update_handlers()
        return res

    async def load_plugins(self, load_list: dict):
        """
        Loads plugins using dict generated by :meth:`discover_plugins()`

        :param load_list: Load list. Usually generated by :meth:`discover_plugins()`
        """
        for plugin in load_list["load_order"]:
            await self.load_plugin(plugin)
        await self.update_handlers()
        return

    async def handle_update(self, context: octobot.Context):
        bot = self
        ctx = context
        ctx.chat_db = database[ctx.chat.id]
        ctx.user_db = database[ctx.user.id]
        current_context.set(context)
        disabled_plugins = []
        async with ctx.chat_db, ctx.user_db:
            if octobot.database.redis is not None and isinstance(context, MessageContext) and context.chat.type == "supergroup":
                disabled_plugins = await octobot.database.redis.smembers(
                    f"plugins_disabled{context.chat.id}")
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
                            await handler.handle_update(bot, ctx)
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
