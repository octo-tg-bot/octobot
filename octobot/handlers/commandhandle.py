import logging
from typing import Union

import octobot.filters
from octobot.utils import deprecated

logger = logging.getLogger("commandhandle")


@deprecated("CommandHandler is deprecated and will be removed in 4.1. Use CommandFilter instead.")
class CommandHandler(octobot.filters.CommandFilter):
    """
    DEPRECATED, Use CommandFilter instead: Command handler. Handles commands in chat and commands in inline queries.

    .. note:: Prefix will not be checked in case of inline queries

    :param command: Command to handle
    :type command: list,str
    :param description: Command description
    :type description: str
    :param long_description: Command long description, appears in help for that specific command
    :type long_description: str
    :param prefix: Command prefix, defaults to `/`
    :type prefix: str,optional
    :param hidden: If command should be hidden from /help, defaults to `False`
    :type hidden: bool,optional
    :param inline_support: If command is supported in inline mode, defaults to `True`
    :type inline_support: bool,optional
    :param service: If command should be excluded from commands list (not from /help)
    :type service: bool,optional
    :param required_args: Required args count, defaults to 0
    :type required_args: int,optional
    """

    # def __init__(self, command: Union[list, str], description: str = "Command description not specified by developer",
    #              long_description: str = "Additional info not specified by developer",
    #              hidden=False, prefix="/", inline_support=True, service: bool = False, required_args: int = 0, *args,
    #              **kwargs):
    #     super(CommandHandler, self).__init__(*args, **kwargs)
    #     if isinstance(command, str):
    #         command = [command]
    #     self.inline_support = inline_support
    #     self.command = command
    #     self.description = description
    #     self.long_description = long_description
    #     self.hidden = hidden
    #     self.prefix = prefix
    #     self.service = service
    #     self.required_args = required_args

    # @property
    # def commandlist(self):
    #     for command in self.command:
    #         yield self.prefix + command

    # def execute_function_textmode(self, bot, context: "octobot.Context"):
    #     try:
    #         self.function(bot, context)
    #     except Exception as e:
    #         octobot.exceptions.handle_exception(bot, context, e)

    # def check_command(self, bot, context):
    #     if isinstance(context, octobot.InlineQueryContext):
    #         if not self.inline_support:
    #             return False
    #         prefix = ''
    #     else:
    #         prefix = self.prefix
    #     incmd = context.text
    #     ratelimit_enabled = Settings.ratelimit.enabled and type(context) == octobot.MessageContext
    #     if ratelimit_enabled:
    #         admin = octobot.check_permissions(chat=context.chat, user=context.user,
    #                                           permissions_to_check={"is_admin"})[
    #                     0] and context.chat.type == "supergroup"
    #         rl_state = Database.redis.get(f"ratelimit_state:{context.chat.id}")
    #         if rl_state == b"user_abuse" and \
    #                 not admin:
    #             return False
    #     if incmd.startswith(prefix):
    #         for command_base in self.command:
    #             command = prefix + command_base
    #             state_only_command = incmd == command or incmd.startswith(
    #                 command + " ")
    #             state_word_swap = len(incmd.split(
    #                 "/")) > 2 and incmd.startswith(command)
    #             state_mention_command = incmd.startswith(
    #                 command + "@" + bot.me.username)
    #             if state_only_command or state_word_swap or state_mention_command:
    #                 context.called_command = command_base
    #                 logger.info("%s called %s using, ctx type is %s", context.user.name, context.called_command, type(context))
    #                 if ratelimit_enabled:
    #                     if admin and Settings.ratelimit.adm_abuse_leave:
    #                         key = f"ratelimit_adm:{context.chat.id}"
    #                     else:
    #                         key = f"ratelimit:{context.chat.id}"
    #                     Database.redis.incr(key)
    #                     Database.redis.expire(key, Settings.ratelimit.messages_timeframe)
    #                 return True
    #     return False

    # def handle_update(self, bot: "octobot.OctoBot", context: "octobot.Context"):
    #     if isinstance(context, octobot.CallbackContext):
    #         return
    #     elif self.check_command(bot, context):
    #         if self.plugin.state == PluginStates.disabled:
    #             context.reply(
    #                 context.localize("Sorry, this command is unavailable. Please contact the bot administrator."))
    #             return
    #         if len(context.args) >= self.required_args:
    #             self.execute_function_textmode(bot, context)
    #         else:
    #             context.reply(context.localize(
    #                 'Not enough arguments! This command takes {args_amount} arguments. ' + \
    #                 'Consider reading <a href="{help_url}">help for this command</a>').format(
    #                 args_amount=self.required_args,
    #                 help_url=bot.generate_startlink(f"/helpextra {self.command[0]}")),
    #                 parse_mode="HTML")
