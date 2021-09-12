import octobot
from settings import Settings

inf = octobot.PluginInfo("Ratelimit", handler_kwargs={
    "CommandHandler": {
        "prefix": "sys!",
        "hidden": True,
        "inline_support": False
    }
}, )
if not Settings.ratelimit.enabled:
    inf.state = octobot.PluginStates.disabled
    inf.state_description = "Ratelimit is disabled in settings"


@octobot.CommandHandler("unban_chat", required_args=1)
@octobot.permissions("is_bot_owner")
def unban(bot, context):
    context.reply("Key delete result:{}".format(octobot.Database.redis.delete(f"ratelimit_state:{context.query}")))


@octobot.MessageHandler(priority=-999)
def handle_rl(bot, context):
    if not isinstance(context, octobot.MessageContext):
        return
    state_key = f"ratelimit_state:{context.chat.id}"
    abuse_state = octobot.Database.redis.get(state_key)
    admin = octobot.check_permissions(chat=context.chat, user=context.user, permissions_to_check={"is_admin"})[0] \
            and context.chat.type == "supergroup"
    if abuse_state is not None:
        abuse_state = abuse_state.decode()
        if abuse_state == "admin_abuse":
            context.reply(context.localize("This chat is permanently blocked in the bot due to command abuse.\n"
                                           "Please contact bot admin at {support_url} to get your chat unbanned.").format(
                support_url=Settings.support_url))
            context.chat.leave()
            raise octobot.StopHandling
    adm_abuse_amount = octobot.Database.redis.get(f"ratelimit_adm:{context.chat.id}")
    abuse_amount = octobot.Database.redis.get(f"ratelimit:{context.chat.id}")
    adm_abuse_amount = int(adm_abuse_amount) if adm_abuse_amount is not None else 0
    abuse_amount = int(abuse_amount) if abuse_amount is not None else 0
    if Settings.ratelimit.adm_abuse_leave and adm_abuse_amount > Settings.ratelimit.messages_threshold:
        inf.logger.info("Banning chat %s", context.chat.id)
        octobot.Database.redis.set(state_key, "admin_abuse")
        return handle_rl.function(bot, context)
    if abuse_amount > Settings.ratelimit.messages_threshold and abuse_state is None:
        octobot.Database.redis.set(state_key, "user_abuse", ex=Settings.ratelimit.ban_time)
        inf.logger.info("Ratelimiting chat %s", context.chat.id)
        if context.chat.type != "private":
            context.reply(context.localize("Users in this chat now temporarily not allowed to use bot commands.\n"
                                           "NOTE: This restriction doesn't apply to admins."))
            if not admin:
                raise octobot.StopHandling
        else:
            context.reply(context.localize("You are now temporarily not allowed to use this bot."))
            raise octobot.StopHandling
