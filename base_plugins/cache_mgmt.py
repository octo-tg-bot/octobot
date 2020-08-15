import octobot
import telegram
inf = octobot.PluginInfo(name=octobot.localizable("Admin cache utils"))

@octobot.CommandHandler(["cache_check", "cache_chk"], description=octobot.localizable("Check group admins cache"))
@octobot.permissions(is_admin=True)
@octobot.supergroup_only
def cache_chk(bot, context):
    cache_msg = []
    cache_msg.append(context.localize("Cache database availability: {}").format(octobot.Database.redis is not None))
    if octobot.Database.redis is not None:
        cache_msg.append(context.localize("Time until current cache death: {}").format(
            octobot.Database.redis.ttl(octobot._perm_db_entry(context.chat))))
        cache_msg.append(context.localize("To reset cache use /cache_reset command"))
    context.reply("\n".join(cache_msg))


@octobot.CommandHandler("cache_reset", "Resets cache")
@octobot.permissions(is_admin=True)
@octobot.supergroup_only
def cache_reset(bot, context):
    octobot.reset_cache(context.chat)
    context.reply(context.localize("Admin cache has been reset"))
