import octobot
import octobot.localization
import gettext
import json
import os


def send_commands(bot: octobot.OctoBot):
    command_list = []
    for priority, priority_handlers in bot.handlers.items():
        for handler in priority_handlers:
            if type(handler) in [octobot.CommandHandler, octobot.CommandFilter]:
                if not (handler.hidden or handler.prefix != "/" or handler.service):
                    for command in handler.command:
                        command_list.append([command, handler.description])
    if os.environ.get("DRY_RUN", False) or bot.test_running:
        os.makedirs("public", exist_ok=True)
        with open("public/commands.json", "w") as f:
            json.dump(command_list, f)
    else:
        bot.set_my_commands(command_list)
        for language in octobot.localization.AVAILABLE_LOCALES:
            command_list_locale = []
            gt = gettext.translation("messages", localedir="locales", languages=[
                language], fallback=True)

            for (command, command_desc) in command_list:
                command_list_locale.append([command, gt.gettext(command_desc)])
                inf.logger.debug("%s -> %s", command_desc,
                                 gt.gettext(command_desc))
            language = language.split("-")[0]
            inf.logger.info("Setting command list for language %s", language)
            bot.set_my_commands(command_list_locale, language_code=language)


inf = octobot.PluginInfo("Command list copier", after_load=send_commands)
