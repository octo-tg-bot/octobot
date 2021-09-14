from octobot.utils import deprecated
from octobot.handlers import BaseHandler


@deprecated("MessageHandler is deprecated and will be removed in 4.1. Use ContextFilter(MessageContext) instead.")
class MessageHandler(BaseHandler):
    """
    Calls function on every message. Simple enough.
    """

    def handle_update(self, bot, context):
        if context.update.message:
            self.function(bot, context)
