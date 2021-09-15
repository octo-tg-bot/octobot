from octobot.enums import PluginStates
from octobot.handlers import BaseHandler
import octobot
import octobot.utils


@octobot.utils.deprecated("InlineButtonHandler is deprecated and will be removed in 4.1. Use octobot.Callback instead.")
class InlineButtonHandler(BaseHandler):
    """
    Inline keyboard button click handler

    .. tip:: You can use :meth:`Context.reply` to show a toast and :meth:`Context.edit` to edit the message

    :param prefix: Prefix. Please end it with some non-letter symbol, like `:`
    """

    def __init__(self, prefix, *args, **kwargs):
        super(type(self),
              self).__init__(*args, **kwargs)
        self.prefix = prefix

    def handle_update(self, bot, context):
        if self.plugin.state == PluginStates.disabled:
            return
        if isinstance(context, octobot.CallbackContext):
            if context.text.startswith(self.prefix):
                try:
                    self.function(bot, context)
                except Exception as e:
                    octobot.handle_exception(bot, context, e)
