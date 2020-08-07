from octobot.handlers import BaseHandler
import octobot
class InlineButtonHandler(BaseHandler):
    def __init__(self, prefix, *args, **kwargs):
        super(InlineButtonHandler, self).__init__(*args, **kwargs)
        self.prefix = prefix

    def handle_update(self, bot, context):
        if context.update_type == octobot.UpdateType.button_press:
            if context.text.startswith(self.prefix):
                self.function(bot, context)
