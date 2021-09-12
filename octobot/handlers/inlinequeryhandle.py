from octobot.enums import PluginStates
from octobot.handlers import BaseHandler
import octobot
class InlineQueryHandler(BaseHandler):
    """
    Inline query click handler

    :param prefix: Prefix to match with
    """
    def __init__(self, prefix, *args, **kwargs):
        super(InlineQueryHandler, self).__init__(*args, **kwargs)
        self.prefix = prefix

    def handle_update(self, bot, context):
        if self.plugin.state == PluginStates.disabled:
            return
        if isinstance(context, octobot.InlineQueryContext):
            if context.text.startswith(self.prefix):
                try:
                    self.function(bot, context)
                except Exception as e:
                    octobot.handle_exception(bot, context, e)
