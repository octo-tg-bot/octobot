import octobot
import json
import os

def send_commands(bot: octobot.OctoBot):
    command_list = []
    for priority, priority_handlers in bot.handlers.items():
        for handler in priority_handlers:
            if isinstance(handler, octobot.handlers.CommandHandler):
                if not (handler.hidden or handler.prefix != "/" or handler.service):
                    for command in handler.command:
                        command_list.append([command, handler.description])
    if os.environ.get("DRY_RUN", False) or bot.test_running:
        os.makedirs("public", exist_ok=True)
        with open("public/commands.json", "w") as f:
            json.dump(command_list, f)
    else:
        bot.set_my_commands(command_list)

inf = octobot.PluginInfo("Command list copier", after_load=send_commands)