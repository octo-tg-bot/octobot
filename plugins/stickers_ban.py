import html

import octobot
import telegram

inf = octobot.PluginInfo(name="Sticker block")


def create_redis_set_name(chat: telegram.Chat):
    return f"stickerban:{chat.id}"


@octobot.CommandHandler(["toggle_pack", "ban_sticker"], description=octobot.localizable("Bans stickerpack in chat"))
@octobot.supergroup_only
@octobot.permissions(can_delete_messages=True)
@octobot.my_permissions(can_delete_messages=True)
def toggle_pack_command(bot: octobot.OctoBot, context: octobot.Context):
    if octobot.Database.redis is None:
        raise octobot.DatabaseNotAvailable
    no_pack_msg = context.localize(
        "Reply to sticker from stickerpack which you want to ban or pass the pack name as argument")
    if context.update.message.reply_to_message is not None:
        if context.update.message.reply_to_message.sticker is not None:
            target_pack = str(context.update.message.reply_to_message.sticker.set_name)
        else:
            return context.reply(no_pack_msg)
    elif len(context.args) > 0:
        target_pack = context.args[0]
    else:
        return context.reply(no_pack_msg)
    if octobot.Database.redis.sadd(create_redis_set_name(context.chat), target_pack) == 1:
        context.reply(context.localize(
            'Pack <a href="https://t.me/addstickers/{pack_id}">{pack_id}</a> banned successfully'.format(
                pack_id=target_pack)), parse_mode="HTML")
    else:
        octobot.Database.redis.srem(create_redis_set_name(context.chat), target_pack)
        context.reply(context.localize(
            'Pack <a href="https://t.me/addstickers/{pack_id}">{pack_id}</a> unbanned successfully'.format(
                pack_id=target_pack)), parse_mode="HTML")


@octobot.CommandHandler(["list_bannedpacks", "list_packbans"],
                        description=octobot.localizable("Lists packs that are banned in this chat"))
@octobot.my_permissions(can_delete_messages=True)
@octobot.supergroup_only
def list_bannedpacks(bot: octobot.OctoBot, context: octobot.Context):
    if octobot.Database.redis is None:
        raise octobot.DatabaseNotAvailable
    if octobot.Database.redis.scard(create_redis_set_name(context.chat)) > 0:
        message = [context.localize("This stickerpacks are currently banned in <b>{chat_name}</b>:").format(
            chat_name=html.escape(context.chat.title))]
        for pack in octobot.Database.redis.smembers(create_redis_set_name(context.chat)):
            message.append('- <a href="https://t.me/addstickers/{pack_id}">{pack_id}</a>'.format(
                pack_id=html.escape(pack.decode())))
        context.reply("\n".join(message), parse_mode="HTML")
    else:
        context.reply(context.localize("There are no stickerpacks that are banned in this chat"))


@octobot.MessageHandler()
@octobot.not_admin
def handle_sticker(bot: octobot.OctoBot, context: octobot.Context):
    if octobot.Database.redis is None:
        return
    if context.update.message.sticker is None:
        return
    packname = str(context.update.message.sticker.set_name)
    if octobot.Database.redis.sismember(create_redis_set_name(context.chat), packname) == 1:
        context.update.message.delete()

