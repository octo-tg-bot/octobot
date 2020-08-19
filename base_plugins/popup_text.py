import octobot

@octobot.InlineButtonHandler("popup_text:")
def popup_text(bot, context):
    text = ":".join(context.text.split(":")[1:])
    context.update.callback_query.answer(text, show_alert=True)
