import html

import babel.dates
import spamwatch
import telegram

import octobot
from settings import Settings
plugin = octobot.PluginInfo("Spamwatch")

def kick(bot: octobot.OctoBot, chat: telegram.Chat, user: telegram.User):
    bot.unban_chat_member(chat.id, user.id)


def ban(bot: octobot.OctoBot, chat: telegram.Chat, user: telegram.User):
    bot.kick_chat_member(chat.id, user.id)


VALID_ACTIONS = {
    "kick": (
        octobot.localizable("Users will be kicked from this chat if they are banned in SpamWatch"),
        kick
    ),
    "ban": (
        octobot.localizable("Users will be banned from this chat if they are banned in SpamWatch"),
        ban),
    "nothing": (
        octobot.localizable("SpamWatch plugin is disabled in this chat."),
        ...)
}
if Settings.spamwatch.default_action not in VALID_ACTIONS:
    plugin.state = octobot.PluginStates.disabled
    plugin.state_description = f"Invalid default action set ({Settings.spamwatch.default_action})"

if Settings.spamwatch.token != "not set":
    SW_CLIENT = spamwatch.Client(Settings.spamwatch.token, host=Settings.spamwatch.api_host)
    plugin.logger.debug("Created spamwatch class OK")
else:
    plugin.logger.error("SW token is N/A (%s)", Settings.spamwatch.token)
    plugin.state = octobot.PluginStates.disabled
    plugin.state_description = f"Spamwatch token is not set"
    SW_CLIENT = None
octobot.localizable("Default")
SPAMWATCH_DB_KEY = "sw_act"

@octobot.Database.cache()
def check_spamwatch_ban(user: telegram.User):
    ban_data = SW_CLIENT.get_ban(user.id)
    return ban_data


@octobot.MessageHandler()
@octobot.not_admin
@octobot.my_permissions("can_restrict_members")
def spamwatch_handle_user(bot: octobot.OctoBot, ctx: octobot.Context):
    if ctx.chat.type != "supergroup":
        return
    chat_action = ctx.chat_db.get(SPAMWATCH_DB_KEY, Settings.spamwatch.default_action)
    if chat_action == "nothing":
        return
    chat_action = VALID_ACTIONS[chat_action]
    banned = check_spamwatch_ban(ctx.user)
    if banned:
        chat_action[-1](bot, ctx.chat, ctx.user)
        bot.send_message(ctx.chat.id, ctx.localize("{user} is banned in SpamWatch since {ban_date}. Reason: <code>{ban_reason}</code>").format(
            user=ctx.user.mention_html(ctx.localize("User")),
            ban_date=babel.dates.format_datetime(banned.date, locale=ctx.locale),
            ban_reason=html.escape(banned.reason)
        ), parse_mode="HTML")

@octobot.CommandHandler("spamwatch_act",
                        description="Sets default action when user that is banned SpamWatch joins or sends message",
                        inline_support=False)
@octobot.supergroup_only
@octobot.permissions("can_change_info")
@octobot.my_permissions("can_restrict_members")
def set_spamwatch_action(bot: octobot.OctoBot, ctx: octobot.Context):
    if len(ctx.args) > 0:
        action = ctx.args[0]
        if action in VALID_ACTIONS:
            ctx.chat_db[SPAMWATCH_DB_KEY] = action
            ctx.reply(ctx.localize("Action {action} set. ").format(action=action) + ctx.localize(VALID_ACTIONS[action][0]))
            return
        else:
            msg = [f'<code>{action}</code> ' + ctx.localize("is not a valid action.")]
    else:
        msg = [
            ctx.localize("You hadn't specified action to set!"),
        ]
    msg.append(ctx.localize("Available actions:"))
    cur_act = ctx.chat_db.get(SPAMWATCH_DB_KEY, Settings.spamwatch.default_action)

    is_default_str = f'<b>({ctx.localize("Default")})</b>'
    for action, (action_desc, _) in VALID_ACTIONS.items():
        msg.append(f"<code>{action}</code> - {ctx.localize(action_desc)} "
                   f"{is_default_str if action == Settings.spamwatch.default_action else ''}")
    msg.append(ctx.localize("Current action in this chat is") + f" <code>{cur_act}</code>")
    ctx.reply("\n".join(msg), parse_mode="HTML")
