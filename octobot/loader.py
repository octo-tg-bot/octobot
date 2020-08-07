import os
from enum import Enum
from glob import glob
import importlib

import telegram

import octobot.handlers
import logging
import jstyleson as json

logger = logging.getLogger("Loader")


class PluginStates(Enum):
    loaded = 0
    unknown = 1
    error = 2
    notfound = 3


def path_to_module(path: str):
    return path.replace("\\", "/").replace("/", ".").replace(".py", "")


class OctoBot(telegram.Bot):
    plugins = {}
    handlers = {}

    def __init__(self, load_list, *args, **kwargs):
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
        if os.path.exists("plugins/load_list.json"):
            with open("plugins/load_list.json") as f:
                load_list = json.load(f)
            plugin_list = []
            for plugin in glob("plugins/*.py"):
                plugin_list.append(path_to_module(plugin))
            plugin_list_diff = list(set(plugin_list) - set(load_list["load_order"]))
            logger.debug("diff: %s, pl: %s", plugin_list_diff, plugin_list)
            if len(plugin_list_diff) > 0:
                logger.warning(
                    "load_order doesnt contain all the files from plugins, adding them into load_order, please check manually")
                load_list["load_order"] += plugin_list_diff
        else:
            logger.error("Failed to find load_list.json, creating one...")
            load_list = {"exclude": [], "load_order": []}
            for item in glob("plugins/*.py"):
                load_list["load_order"].append(item)
        new_ll = []
        for plugin in load_list["load_order"]:

            plugin = path_to_module(plugin)
            new_ll.append(plugin)
        load_list["load_order"] = new_ll
        with open("plugins/load_list.json", 'w') as f:
            json.dump(load_list, f)
        return load_list

    def update_handlers(self):
        self.handlers = {}
        for plugin in self.plugins.values():
            plugin = plugin["module"]
            for var_name in dir(plugin):
                var = getattr(plugin, var_name)
                if isinstance(var, octobot.handlers.BaseHandler):
                    if var.priority not in self.handlers:
                        self.handlers[var.priority] = []
                    self.handlers[var.priority].append(var)
        logger.info("Handlers update complete, priority levels: %s", self.handlers.keys())

    def load_plugin(self, plugin: str, single_load=False):
        self.plugins[plugin] = dict(name=plugin, state=PluginStates.unknown, module=None)
        try:
            plugin_module = importlib.import_module(plugin)
        except ModuleNotFoundError:
            self.plugins[plugin]["state"] = PluginStates.notfound
            logger.error("Plugin %s is defined in load_order, but cannot be found. Please check your load_list.json", plugin)
        except Exception as e:
            logger.error("Failed to load plugin %s", exc_info=True)
            self.plugins[plugin]["state"] = PluginStates.error
        else:
            self.plugins[plugin]["state"] = PluginStates.loaded
            self.plugins[plugin]["module"] = plugin_module
            logger.info("Loaded plugin %s", plugin)
        if single_load:
            self.update_handlers()
        return

    def load_plugins(self, load_list: dict):
        for plugin in load_list["load_order"]:
            if not plugin in load_list["exclude"]:
                self.load_plugin(plugin)
        self.update_handlers()
        return

    def handle_update(self, bot, update):
        try:
            ctx = octobot.Context(update)
        except octobot.UnknownUpdate:
            logger.warning("Failed to determine update type: %s", update.to_dict())
        for handlers in self.handlers.values():
            try:
                for handler in handlers:
                    try:
                        handler.handle_update(bot, ctx)
                    except octobot.StopHandling as e:
                        raise e
                    except Exception as e:
                        logger.error("Handler threw an exception!", exc_info=True)
            except octobot.StopHandling:
                break
