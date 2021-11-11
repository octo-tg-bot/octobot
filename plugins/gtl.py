import html

import babel
import googletrans
from cachetools import cached, TTLCache

import octobot
from octobot.dataclass import Suggestion
import octobot.localization

inf = octobot.PluginInfo(octobot.localizable("Google Translate"))


@cached(cache=TTLCache(maxsize=1, ttl=90))
def get_translator():
    inf.logger.debug("Creating translator class")
    return googletrans.Translator()


TRANSLATION_TEMPLATE = octobot.localizable(
    "From <i>{source_language}</i> to <i>{target_language}</i>\n<code>{text}</code>")


@octobot.CommandHandler(["tl", "translate"], description=octobot.localizable("Translates text using Google Translate"), suggestion=Suggestion(None, "Google Translate", "tl en-ru hello"))
def gtl(bot: octobot.OctoBot, context: octobot.Context):
    translator = get_translator()
    if context.update.message is not None and context.reply_to_message is not None:
        text = context.reply_to_message.text or context.reply_to_message.caption
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
    if not destination_language.startswith("zh"):
        destination_language = destination_language.split("-")[0]
    inf.logger.debug("dest lang %s", destination_language)
    if text is None or len(text) == 0:
        return context.reply(context.localize("No text to translate was specified/replied to!"))
    translation = translator.translate(
        text, dest=destination_language, src=source_language)
    base_l = context.locale
    src = base_l.languages.get(translation.src.replace(
        "_", "-").split("-")[0].lower(), translation.src)
    dest = base_l.languages.get(destination_language.replace(
        "_", "-").split("-")[0].lower(), destination_language)
    return context.reply(context.localize(TRANSLATION_TEMPLATE).format(
        source_language=src,
        target_language=dest,
        text=html.escape(translation.text)
    ), parse_mode="HTML")
