import html

import googletrans

import octobot
import octobot.localization

translator = googletrans.Translator()

inf = octobot.PluginInfo(octobot.localizable("Google Translate"))

TRANSLATION_TEMPLATE = octobot.localizable("From <i>{source_language}</i> to <i>{target_language}</i>\n<code>{text}</code>")


@octobot.CommandHandler(["tl", "translate"], description=octobot.localizable("Translates text using Google Translate"))
def gtl(bot: octobot.OctoBot, context: octobot.Context):
    if context.update.message is not None and context.update.message.reply_to_message is not None:
        text = context.update.message.reply_to_message.text
        text_type = "reply"
    else:
        text = str(context.query)
        text_type = "args"
    source_language = None
    destination_language = None
    default_language = octobot.localization.get_chat_locale(context.update)
    if len(context.args) > 0:
        arg_0 = context.args[0]
        if arg_0 in googletrans.LANGUAGES:
            destination_language = arg_0
            destination_language.replace("_", "-")
            if text_type == "args":
                text = " ".join(context.args[1:])
        elif arg_0.count("-") == 1:
            source_language, destination_language = arg_0.split("-")
            source_language.replace("_", "-")
            destination_language.replace("_", "-")
            if text_type == "args":
                text = " ".join(context.args[1:])
    if source_language not in googletrans.LANGUAGES:
        source_language = "auto"
    if destination_language not in googletrans.LANGUAGES:
        destination_language = default_language
    translation = translator.translate(text, dest=destination_language, src=source_language)
    return context.reply(context.localize(TRANSLATION_TEMPLATE).format(
        source_language=googletrans.LANGUAGES[translation.src].title(),
        target_language=googletrans.LANGUAGES[translation.dest].title(),
        text=html.escape(translation.text)
    ), parse_mode="HTML")
