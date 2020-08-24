import html

import telegram

import octobot
import typing

inf = octobot.PluginInfo(
    name=octobot.localizable("Admin commands"),
    reply_kwargs={"editable": False}
)


def lookup_username(target):
    if octobot.database.redis is None:
        return False, 0
    uname_key = generate_uname_key(target)
    if octobot.Database.redis.exists(uname_key):
        return True, int(octobot.Database.redis.get(uname_key))
    return False, 0


def execute_cancel(bot: octobot.OctoBot, context: octobot.Context, func: typing.Callable, reply_text: str):
    tgt_id, chat_id = context.text.split(":")[1:]
    perm_check, missing_perms = octobot.check_permissions(chat=chat_id, user=context.user.id, bot=bot,
                                                          permissions_to_check={"can_restrict_members"})
    if perm_check:
        if tgt_id.isdigit():
            func(chat_id=chat_id, user_id=tgt_id)
            context.reply(reply_text)
            msg = context.update.effective_message.text_html + "\n\n" + context.localize(
                'This action was undone by <a href="tg://user?id={admin_id}">{admin}</a>').format(
                admin_id=context.user.id,
                admin=html.escape(context.user.first_name)
            )
            context.edit(msg, parse_mode="HTML")
        else:
            context.reply(context.localize("Invalid ID passed"))
    else:
        context.reply(
            context.localize("Sorry, you can't execute this command cause you lack following permissions: {}").format(
                ", ".join(missing_perms)))


def execute_command(func: typing.Callable, context: octobot.Context, success_message: str, action: str,
                    cancel: str = None):
    reply = context.update.message.reply_to_message
    if reply is not None:
        target = reply.from_user.id
        target_name = reply.from_user.first_name
    elif len(context.args) > 0:
        target = context.args[0]
        target_name = f"ID:{target}"
        if not target.isdigit():
            if target.startswith("@"):
                target = target[1:]
            target_name = f"@{target}"
            success, target = lookup_username(target)
            if not success:
                context.reply(context.localize("I hadn't seen the person whose username is @{username}").format(target))
                return
        else:
            target = int(target)
    else:
        context.reply(
            context.localize(
                "You hadn't specified the target!" + \
                "Reply to message of person you want to {action} or specify their ID or username").format(
                action=action))
        return
    if octobot.check_permissions(chat=context.chat, user=target,
                                 permissions_to_check={"is_admin"})[0]:
        context.reply(
            context.localize("I can't {action} administrators.").format(action=action)
        )
        return
    try:
        func(chat_id=context.chat.id, user_id=target)
    except telegram.error.BadRequest as e:
        context.reply(
            context.localize(
                'Can\'t {action} <a href="tg://user?id={target}">{target_name}</a>.\nError: <code>{error}</code>.').format(
                action=action,
                target=html.escape(target_name),
                error=html.escape(e.message)),
            parse_mode="html")
    else:
        cancel_markup = None
        if cancel is not None:
            cancel_markup = telegram.InlineKeyboardMarkup.from_button(telegram.InlineKeyboardButton(
                text=context.localize("Cancel"),
                callback_data=f"{cancel}:{target}:{context.chat.id}"
            ))
        context.reply(success_message.format(admin_name=html.escape(context.user.first_name),
                                             admin_id=context.user.id,
                                             target=target,
                                             target_name=html.escape(target_name)),
                      parse_mode="html",
                      reply_markup=cancel_markup)


@octobot.CommandHandler("ban", octobot.localizable("Bans user in this chat"))
@octobot.permissions(can_restrict_members=True)
@octobot.my_permissions(can_restrict_members=True)
@octobot.supergroup_only
def command_ban(bot: octobot.OctoBot, context: octobot.Context):
    execute_command(bot.kick_chat_member, context,
                    context.localize('🔨<a href="tg://user?id={admin_id}">{admin_name}</a> banned ' + \
                                     '<a href="tg://user?id={target}">{target_name}</a>'),
                    action=context.localize("ban"),
                    cancel="ban_cancel")


@octobot.CommandHandler("kick", octobot.localizable("Kicks user from chat"))
@octobot.permissions(can_restrict_members=True)
@octobot.my_permissions(can_restrict_members=True)
@octobot.supergroup_only
def command_kick(bot: octobot.OctoBot, context: octobot.Context):
    execute_command(bot.unban_chat_member, context,
                    context.localize('👞<a href="tg://user?id={admin_id}">{admin_name}</a> kicked ' + \
                                     '<a href="tg://user?id={target}">{target_name}</a>'),
                    action=context.localize("kick")
                    )


@octobot.InlineButtonHandler("ban_cancel:")
def command_ban_cancel(bot: octobot.OctoBot, context: octobot.Context):
    execute_cancel(bot, context, reply_text=context.localize("Unbanned"), func=bot.unban_chat_member)


def pin(bot, context, loud=False):
    if context.update.message.reply_to_message is None:
        context.reply("Reply to message you want to pin")
        return
    old_pin = bot.get_chat(context.chat.id).pinned_message
    old_pin_message = ""
    reply_markup = None
    if old_pin is not None:
        reply_markup = telegram.InlineKeyboardMarkup.from_button(
            telegram.InlineKeyboardButton(callback_data=f"pin:{context.chat.id}:{old_pin.message_id}",
                                          text=context.localize("Pin back the old message")))
        old_pin_message = context.localize('\n<a href="{oldpin_link}">Old pinned message</a>').format(
            oldpin_link=old_pin.link)
    bot.pin_chat_message(chat_id=context.chat.id,
                         message_id=context.update.message.reply_to_message.message_id,
                         disable_notification=not loud)
    context.reply(context.localize('📌<a href="tg://user?id={admin_id}">{admin}</a> pinned message.\n').format(
        admin_id=context.user.id,
        admin=html.escape(context.user.first_name)
    ) + old_pin_message,
                  reply_markup=reply_markup,
                  parse_mode="HTML")


@octobot.CommandHandler("pin", octobot.localizable("Pins message in chat"))
@octobot.permissions(can_pin_messages=True)
@octobot.my_permissions(can_pin_messages=True)
@octobot.supergroup_only
def command_pin(bot: octobot.OctoBot, context: octobot.Context):
    pin(bot, context, loud=False)


@octobot.CommandHandler("pin_loud", octobot.localizable("Pins message in chat with notification"))
@octobot.permissions(can_pin_messages=True)
@octobot.my_permissions(can_pin_messages=True)
@octobot.supergroup_only
def command_pin_loud(bot: octobot.OctoBot, context: octobot.Context):
    pin(bot, context, loud=True)


@octobot.InlineButtonHandler("pin:")
def button_pin(bot: octobot.OctoBot, context: octobot.Context):
    chat_id, message_id = context.text.split(":")[1:]
    perm_check, missing_perms = octobot.check_permissions(chat=chat_id, user=context.user.id, bot=bot,
                                                          permissions_to_check={"can_pin_messages"})
    if perm_check:
        bot.pin_chat_message(chat_id, message_id, disable_notification=True)
        context.reply(context.localize("Pinned back the old message"))
        msg = context.update.effective_message.text_html + "\n\n" + context.localize(
            'This action was undone by <a href="tg://user?id={admin_id}">{admin}</a>').format(
            admin_id=context.user.id,
            admin=html.escape(context.user.first_name)
        )
        context.edit(msg, parse_mode="HTML")
    else:
        context.reply(
            context.localize("Sorry, you can't execute this command cause you lack following permissions: {}").format(
                ", ".join(missing_perms)))


def create_warn_db_id(chat_id, user_id):
    return f"warns:{chat_id}:{user_id}"


@octobot.CommandHandler("warn", octobot.localizable("Gives user a warning"))
@octobot.permissions(can_restrict_members=True)
@octobot.my_permissions(can_restrict_members=True)
@octobot.supergroup_only
def warn(bot: octobot.OctoBot, context: octobot.Context):
    if octobot.Database.redis is None:
        raise octobot.DatabaseNotAvailable
    if context.update.message.reply_to_message is None:
        context.reply(context.localize("Reply to user to give them a warn"))
        return
    if octobot.check_permissions(chat=context.chat, user=context.update.message.reply_to_message.from_user,
                                 permissions_to_check={"is_admin"})[0]:
        context.reply(context.localize("Can't warn administrator"))
        return
    target_id = context.update.message.reply_to_message.from_user.id
    target_name = context.update.message.reply_to_message.from_user.first_name
    user_warns_db_id = create_warn_db_id(context.chat.id, target_id)
    max_warns = int(context.chat_db.get("max_warns", 3))
    reason = context.query
    if reason == "":
        reason = context.localize("Warn reason not specified")
    octobot.Database.redis.lpush(user_warns_db_id, reason)
    user_warn_count = int(octobot.Database.redis.llen(user_warns_db_id))
    action_taken = ""
    reply_markup = telegram.InlineKeyboardMarkup.from_button(
        telegram.InlineKeyboardButton(text="Remove last warn",
                                      callback_data=f"warn_cancel:{target_id}:{context.chat.id}"))
    if user_warn_count >= max_warns:
        action_taken = context.localize("\n\n<i>User had reached maximum warnings in chat and was banned</i>")
        bot.kick_chat_member(chat_id=context.chat.id, user_id=target_id)
        octobot.Database.redis.delete(user_warns_db_id)
        reply_markup = telegram.InlineKeyboardMarkup.from_button(telegram.InlineKeyboardButton(
            callback_data=f"ban_cancel:{target_id}:{context.chat.id}",
            text=context.localize("Unban")
        ))
    context.reply(context.localize('⚠️<a href="tg://user?id={admin_id}">{admin}</a> warned ' + \
                                   '<a href="tg://user?id={target_id}">{target_name}</a> ' + \
                                   '({warn_count}/{max_warns})' + \
                                   '\nReason: <i>{reason}</i>').format(
        admin_id=context.user.id,
        admin=html.escape(context.user.first_name),
        target_id=target_id,
        target_name=html.escape(target_name),
        reason=html.escape(reason),
        warn_count=user_warn_count,
        max_warns=max_warns
    ) + action_taken, parse_mode="HTML",
                  reply_markup=reply_markup)


def undo_warn(chat_id, user_id):
    user_warns_db_id = create_warn_db_id(chat_id, user_id)
    octobot.Database.redis.lpop(user_warns_db_id)


@octobot.InlineButtonHandler("warn_cancel:")
def inline_undo_warn(bot: octobot.OctoBot, context: octobot.Context):
    if octobot.Database.redis is None:
        raise octobot.DatabaseNotAvailable
    execute_cancel(bot=bot, context=context, func=undo_warn, reply_text=context.localize("Warn removed"))


@octobot.CommandHandler("warnlist", octobot.localizable("Lists all user warns or your warns"))
@octobot.supergroup_only
def warnlist(bot: octobot.OctoBot, context: octobot.Context):
    if octobot.Database.redis is None:
        raise octobot.DatabaseNotAvailable
    reply = context.update.message.reply_to_message
    if reply is not None:
        target = reply.from_user.id
        target_name = reply.from_user.first_name
    elif len(context.args) > 0:
        target = context.args[0]
        if target.isdigit():
            target = int(target)
            target_name = f"ID:{target}"
        else:
            if target.startswith("@"):
                target = target[1:]
            target_name = target
            res, target = lookup_username(target)
            if not res:
                return context.reply(
                    context.localize("Failed to find username {username}").format(username=target_name))
    else:
        target = context.user.id
        target_name = context.user.first_name
    message = [context.localize("Warns for {name}:").format(name=target_name)]
    warns = octobot.Database.redis.lrange(create_warn_db_id(context.chat.id, target), 0, -1)
    if len(warns) == 0:
        context.reply(context.localize("{name} has no warns!").format(name=target_name))
    else:
        for warn_reason in warns:
            message.append(f"- {warn_reason.decode()}")
        context.reply("\n".join(message))


def generate_uname_key(username):
    return f"username:{username.lower()}"


@octobot.MessageHandler()
def username_cache(bot: octobot.OctoBot, context: octobot.Context):
    if octobot.Database.redis is None:
        return
    if context.user.username is None or context.user.username == "":
        return
    uname_key = generate_uname_key(context.user.username)
    if octobot.Database.redis.exists(uname_key) == 0:
        octobot.Database.redis.set(uname_key, context.user.id)
        octobot.Database.redis.expire(uname_key, 60 * 60 * 24 * 30)
