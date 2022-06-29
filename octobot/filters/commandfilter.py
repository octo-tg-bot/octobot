from typing import Union
import octobot
from .basefilters import BaseFilter
from .permissionfilter import check_permissions
import logging

logger = logging.getLogger('commandfilter')


class CommandFilter(BaseFilter):
    _filterWeight = 10
    loud_exceptions = True

    def __init__(self, command: Union[list, str], description: str = "Command description not specified by developer",
                 long_description: str = "Additional info not specified by developer",
                 hidden=False, prefix="/", service: bool = False, required_args: int = 0, suggestion=None, *args,
                 **kwargs):
        super(CommandFilter, self).__init__(*args, **kwargs)
        if isinstance(command, str):
            command = [command]
        self.command = command
        self.description = description
        self.long_description = long_description
        self.hidden = hidden
        self.prefix = prefix
        self.service = service
        self.required_args = required_args
        self.suggestion = suggestion

    async def check_command(self, bot, context):
        if isinstance(context, octobot.InlineQueryContext):
            prefix = ''
        else:
            prefix = self.prefix
        incmd = context.text
        ratelimit_enabled = octobot.settings.ratelimit.enabled and type(
            context) == octobot.MessageContext
        if ratelimit_enabled:
            admin = (await check_permissions(chat=context.chat, user=context.user,
                                             permissions_to_check={"is_admin"}))[
                0] and context.chat.type == "supergroup"
            rl_state = await octobot.database.redis.get(
                f"ratelimit_state:{context.chat.id}")
            if rl_state == b"user_abuse" and \
                    not admin:
                return False
        if incmd.startswith(prefix):
            for command_base in self.command:
                command = prefix + command_base
                state_only_command = incmd == command or incmd.startswith(
                    command + " ")
                state_word_swap = len(incmd.split(
                    "/")) > 2 and incmd.startswith(command)
                state_mention_command = incmd.startswith(
                    command + "@" + bot.me.username)
                if state_only_command or state_word_swap or state_mention_command:
                    context.called_command = command_base
                    logger.info("%s called %s using, ctx type is %s",
                                context.user.name, context.called_command, type(context))
                    if ratelimit_enabled:
                        if admin and octobot.settings.ratelimit.adm_abuse_leave:
                            key = f"ratelimit_adm:{context.chat.id}"
                        else:
                            key = f"ratelimit:{context.chat.id}"
                        await octobot.database.redis.incr(key)
                        await octobot.database.redis.expire(
                            key, octobot.settings.ratelimit.messages_timeframe)
                    return True
        return False

    async def validate(self, bot: "octobot.OctoBot", context: "octobot.Context"):
        if isinstance(context, octobot.CallbackContext):
            return False
        elif await self.check_command(bot, context):
            if getattr(self.plugin, 'state', 'ok') == octobot.PluginStates.disabled:
                context.reply(
                    context.localize("Sorry, this command is unavailable. Please contact the bot administrator."))
                return False
            if len(context.args) >= self.required_args:
                return True
            else:
                context.reply(context.localize(
                    'Not enough arguments! This command takes {args_amount} arguments. ' +
                    'Consider reading <a href="{help_url}">help for this command</a>').format(
                    args_amount=self.required_args,
                    help_url=bot.generate_startlink(f"/helpextra {self.command[0]}")),
                    parse_mode="HTML")
                return False

    @property
    def commandlist(self):
        for command in self.command:
            yield self.prefix + command
