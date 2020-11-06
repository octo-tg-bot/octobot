import datetime

import pytz

from octobot import CommandHandler, Context, OctoBot, PluginInfo, localizable

plugin_info = PluginInfo(localizable("User ID"))


@CommandHandler(command="id",
                description=localizable("Check the user/group/message/inline_query IDs"))
def ping(bot: OctoBot, ctx: Context):
    user_id = ctx.user.id
    if ctx.update.message:
        chat_id = ctx.update.message.chat.id
        chat_type = ctx.update.message.chat.type
    elif ctx.update.inline_query:
        chat_id = "None"
        chat_type = "Inline Query"
    else:
        return ctx.reply("Cant understand what is going on in that update of yours")
    message = [ctx.localize("{} ID:<code>{}</code>").format(ctx.user.mention_html(ctx.localize("Your")), user_id),
               ctx.localize("Chat ID:<code>{}</code>").format(chat_id),
               ctx.localize("Chat type is <code>{}</code>").format(chat_type)]
    if ctx.update.message:
        msg = ctx.update.message
        message.append(ctx.localize("ID of your message: <code>{}</code>").format(ctx.update.message.message_id))
        if msg.reply_to_message:
            reply = msg.reply_to_message
            message.append(ctx.localize("ID of replied message: <code>{}</code>").format(reply.message_id))
            if reply.from_user.id:
                message.append(ctx.localize("ID of {} from replied message: {}").format((reply.from_user.mention_html("user")), reply.from_user.id))
            if reply.forward_from:
                message.append(ctx.localize("Forward {} ID: {}").format((reply.forward_from.mention_html("user")), reply.forward_from.id))
            if reply.forward_from_message_id:
                message.append(ctx.localize("Forwarded message ID in original chat: {}").format(reply.forward_from_message_id))
            if reply.forward_from_chat:
                message.append(ctx.localize("Forwarded message original chat ({}) ID: {}").format(reply.forward_from_chat.title, reply.forward_from_chat.id))
    ctx.reply("\n".join(message), parse_mode='html')
