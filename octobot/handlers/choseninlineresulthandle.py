from octobot.enums import PluginStates
from octobot.handlers import BaseHandler
import octobot
class ChosenInlineResultHandler(BaseHandler):
    """
    Inline query chosen result handler

    :param result_id: Prefix for ChosenInlineResult.id to match against
    """
    def __init__(self, prefix, *args, **kwargs):
        super(ChosenInlineResultHandler, self).__init__(*args, **kwargs)
        self.prefix = prefix

    def handle_update(self, bot, context):
        if self.plugin.state == PluginStates.disabled:
            return
        if context.update_type == octobot.UpdateType.chosen_inline_result:
            if context.update.chosen_inline_result.result_id.startswith(self.prefix):
                try:
                    self.function(bot, context)
                except Exception as e:
                    octobot.handle_exception(bot, context, e)
