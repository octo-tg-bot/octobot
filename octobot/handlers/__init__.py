from octobot.classes import PluginInfo


class BaseHandler:
    """Base class for all handlers"""
    plugin = {"plugin_info": PluginInfo("unknown")}

    def __init__(self, priority=0):
        self.priority = priority

    def handle_update(self, bot, update):
        raise RuntimeError("handle_update in handler not overridden!")

    def __call__(self, *args, **kwargs):
        self.function = args[0]
        return self


class ExceptionHandler:
    def handle_exception(self, bot, context, exception):
        return

class MessageHandler(BaseHandler):
    """
    Calls function on every message. Simple enough.
    """

    def handle_update(self, bot, context):
        if context.update.message:
            self.function(bot, context)


from octobot.handlers.buttonhandle import InlineButtonHandler
from octobot.handlers.commandhandle import CommandHandler
