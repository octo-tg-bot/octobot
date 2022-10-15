import telegram
from telegram.inline.inputmessagecontent import InputMessageContent
from telegram.inline.inputtextmessagecontent import InputTextMessageContent
import octobot
from octobot.classes import PluginInfo
from settings import Settings
import random
inf = PluginInfo("Inline Fallback")


def get_commands(bot: octobot.OctoBot):
    inline_commands = []
    inline_unsupported_commands = []
    suggestions = []
    for commands in bot.handlers.values():
        for command in commands:
            if isinstance(command, octobot.CommandFilter):
                if command.inline_support:
                    inline_commands += command.command
                    if suggestion := getattr(command, "suggestion", False):
                        suggestions.append(suggestion)
                else:
                    inline_unsupported_commands += command.command
    return inline_commands, inline_unsupported_commands, suggestions


@octobot.InlineQueryHandler("", priority=-100)
def inline_handler(bot: octobot.OctoBot, context: octobot.InlineQueryContext):
    inline_commands, noninline_commands, suggestions = get_commands(bot)
    inf.logger.debug("inline commands: %s", inline_commands)
    inf.logger.debug("noninline commands: %s", noninline_commands)
    inf.logger.debug("suggestions: %s", suggestions)
    query = context.update.inline_query
    supplied_command = query.query.split(" ")[0]
    if supplied_command in inline_commands:
        return
    if len(suggestions) == 0:
        suggestions = [
            octobot.Suggestion(
                icon=None,
                title="No suggestions installed.", example_command="no")
        ]
    selected_suggestion = random.choice(suggestions)
    suggestion = telegram.InlineQueryResultArticle(f"suggestion-{selected_suggestion.title}",
                                                   title=context.localize("Maybe try {suggestionCommandTitle}?").format(
                                                       suggestionCommandTitle=selected_suggestion.title),
                                                   description=context.localize("Try: {commandExample}").format(
                                                       commandExample=selected_suggestion.example_command),
                                                   input_message_content=InputTextMessageContent(context.localize(
                                                       "You aren't supposed to press it")),
                                                   thumb_url=selected_suggestion.icon,
                                                   thumb_height=512,
                                                   thumb_width=512
                                                   )
    if supplied_command in noninline_commands:
        query.answer([suggestion],
                     switch_pm_parameter="help",
                     switch_pm_text=context.localize(
                         "{suppliedCommand} doesn't work inline").format(suppliedCommand=supplied_command),
                     cache_time=(360 if Settings.production else 0))
        return
    if supplied_command == "":
        query.answer([suggestion],
                     switch_pm_parameter="help",
                     switch_pm_text=context.localize(
                         "Click here for command list"),
                     cache_time=(360 if Settings.production else 0))
        return
    if supplied_command not in noninline_commands:
        query.answer([suggestion],
                     switch_pm_parameter="help",
                     switch_pm_text=context.localize(
            "Unknown command - click here for command list"),
            cache_time=(360 if Settings.production else 0))
        return
