class BaseHandler():
    def __init__(self, priority=0):
        self.priority = priority

    def handle_update(self, bot, update):
        raise RuntimeError("handle_update in handler not overridden!")

    def __call__(self, *args, **kwargs):
        self.function = args[0]
        return self


class MessageHandler(BaseHandler):
    def handle_update(self, bot, update):
        if update.message:
            self.function(bot, update)

from octobot.handlers.buttonhandle import InlineButtonHandler
from octobot.handlers.commandhandle import CommandHandler
from octobot.handlers.cataloghandler import CatalogHandler