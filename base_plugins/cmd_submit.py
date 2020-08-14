import octobot
import telegram

def send_commands(bot: octobot.OctoBot):
    command_list = []
    for priority, priority_handlers in bot.handlers.items():
        for handler in priority_handlers:
            if isinstance(handler, octobot.CommandHandler):
                if not (handler.hidden or handler.prefix != "/"):
                    for command in handler.command:
                        command_list.append(telegram.BotCommand(command=command, description=handler.description))
    bot.set_my_commands(command_list)

inf = octobot.PluginInfo("Command list copier", after_load=send_commands)