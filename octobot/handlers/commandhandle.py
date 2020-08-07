import octobot
from octobot.handlers import BaseHandler
from typing import Union


class CommandHandler(BaseHandler):
    def __init__(self, command: Union[list, str], description: str = "Command description not specified by developer",
                 hidden=False, prefix="/", *args, **kwargs):
        super(CommandHandler, self).__init__(*args, **kwargs)
        if isinstance(command, str):
            command = [command]
        self.command = command
        self.description = description
        self.hidden = hidden
        self.prefix = prefix

    def execute_function_textmode(self, bot, context):
        self.function(bot, context)

    def handle_update(self, bot, context):
        incmd = context.text
        if context.update_type == octobot.UpdateType.button_press:
            return
        elif context.update_type == octobot.UpdateType.inline_query:
            prefix = ''
        else:
            prefix = self.prefix
        print('prefix:', repr(prefix))
        if incmd.startswith(prefix):
            for command in self.command:
                command = prefix + command
                state_only_command = incmd == command or incmd.startswith(
                    command + " ")
                state_word_swap = len(incmd.split(
                    "/")) > 2 and incmd.startswith(command)
                state_mention_command = incmd.startswith(
                    command + "@" + bot.me.username)
                if state_only_command or state_word_swap or state_mention_command:
                    self.execute_function_textmode(bot, context)
