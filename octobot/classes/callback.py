class Callback:
    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def execute(self, bot, context):
        return self.function(bot, context, *self.args, **self.kwargs)


def invalid_callback(bot, ctx):
    ctx.reply(ctx.localize(
        "I can't understand what this inline button does. The keyboard here is probably outdated."))


def empty_callback(bot, ctx):
    ctx.reply(ctx.localize("You saw nothing"))


InvalidCallback = Callback(invalid_callback)
EmptyCallback = Callback(empty_callback)


class PopupCallback(Callback):
    def __init__(self, popup_text):
        self.popup_text = popup_text

    def execute(self, bot, context):
        context.update.callback_query.answer(self.popup_text, show_alert=True)
