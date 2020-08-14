from octobot import PluginInfo


class BaseHandler():
    """Base class for all handlers"""
    plugin = {"plugin_info": PluginInfo("unknown")}
    def __init__(self, priority=0):
        self.priority = priority

    def handle_update(self, bot, update):
        raise RuntimeError("handle_update in handler not overridden!")

    def __call__(self, *args, **kwargs):
        self.function = args[0]
        return self


class MessageHandler(BaseHandler):
    """
    Calls function on every message. Simple enough.
    """
    def handle_update(self, bot, update):
        if update.message:
            self.function(bot, update)

from octobot.handlers.buttonhandle import InlineButtonHandler
from octobot.handlers.commandhandle import CommandHandler
