import logging
import typing

import octobot
from octobot.database import Database
import telegram
import json

from settings import Settings

permissions_locale = {
    "is_bot_owner": octobot.localizable("bot owner. Who the fu - Who is - What - I should kick your fucking ass, "
                                        "who is this?"),
    "can_change_info": octobot.localizable("change chat info"),
    "is_admin": octobot.localizable("chat admin"),
    "can_delete_messages": octobot.localizable("delete messages"),
    "can_restrict_members": octobot.localizable("restrict members"),
    "can_pin_messages": octobot.localizable("pin messages"),
    "can_promote_members": octobot.localizable("promote members"),
    "can_manage_chat": octobot.localizable("manage chat"),
    "can_manage_voice_chats": octobot.localizable("manage voice chats")
}
logger = logging.getLogger("permissions")

def create_db_entry_name(chat: typing.Union[telegram.Chat, int]):
    if isinstance(chat, telegram.Chat):
        chat = chat.id
    return f"admcache:{chat}"


def reset_cache(chat: typing.Union[telegram.Chat, int]):
    return Database.redis.delete(create_db_entry_name(chat))


def check_perms(chat: typing.Union[telegram.Chat, int], user: typing.Union[telegram.User, int],
                permissions_to_check: set, bot=None):
    db_entry = create_db_entry_name(chat)

    if isinstance(user, telegram.User):
        user_id = user.id
    else:
        user_id = user
    if isinstance(chat, telegram.Chat):
        chat_id = chat.id
    else:
        chat_id = chat
    if "is_bot_owner" in permissions_to_check:
        if Settings.owner == user_id: permissions_to_check.remove("is_bot_owner")
        return Settings.owner == user_id, permissions_to_check
    if not str(chat_id).startswith("-100"):
        return True, []
    if Database.redis is not None and Database.redis.exists(db_entry) == 1:
        adm_list = json.loads(Database.redis.get(db_entry).decode())
    else:
        if bot is None:
            adm_list_t = chat.get_administrators()
        else:
            adm_list_t = bot.get_chat_administrators(chat_id=chat_id)
        adm_list = []
        for admin in adm_list_t:
            adm_list.append(admin.to_dict())
        if Database.redis is not None:
            Database.redis.set(db_entry, json.dumps(adm_list))
            Database.redis.expire(db_entry, 240)
    for member in adm_list:
        if int(member["user"]["id"]) == int(user_id):
            if member["status"] == "creator":
                return True, []
            if "is_admin" in permissions_to_check:
                permissions_to_check.remove("is_admin")
            for user_permission in permissions_to_check.copy():
                if member[user_permission]:
                    permissions_to_check.remove(user_permission)
            break
    return len(permissions_to_check) == 0, permissions_to_check


def permissions(*perms_args, **perms_kwargs):
    """
    Decorator to check permissions.

    :param perms: Valid permissions that can be found on :class:`telegram.ChatMember` + is_admin. Example: `@permissions(can_delete_messages=True)`. The value does not matter.
    """
    perms = set(perms_kwargs.keys())
    perms.update(perms_args)
    for permission in perms:
        if permission not in permissions_locale:
            logger.error("Unknown permission: %s", permission)
            raise IndexError(f"Unknown permission: {permission}")

    def decorator(function):
        def wrapper(bot, context):
            if context.chat is not None:
                res, missing_perms = check_perms(context.chat, context.user, perms.copy())
                missing_perms_localized = [context.localize(permissions_locale[permission]) for permission in missing_perms]
                if res:
                    function(bot, context)
                else:
                    context.reply(context.localize(
                        "Sorry, you can't execute this command cause you lack following permissions: {}").format(
                        ', '.join(missing_perms_localized)))

        return wrapper

    return decorator


def not_admin(function):
    """
    Decorator to check if sender is not an admin.
    """
    perms = {"is_admin"}

    def wrapper(bot, context):
        if context.chat is not None:
            res, missing_perms = check_perms(context.chat, context.user, perms.copy())
            if not res:
                function(bot, context)

    return wrapper


def my_permissions(*perms_args, **perms_kwargs):
    """
    Decorator to check bots own permissions.

    :param perms: Valid permissions that can be found on :class:`telegram.ChatMember` + is_admin. Example: `@my_permissions(can_delete_messages=True)`. The value does not matter.
    """
    perms = set(perms_kwargs.keys())
    perms.update(perms_args)
    if "is_admin" not in perms:
        perms.add("is_admin")

    def decorator(function):
        def wrapper(bot, context):
            if context.chat is not None:
                res, missing_perms = check_perms(context.chat, bot.me, perms.copy())
                if res:
                    function(bot, context)
                elif "is_admin" not in missing_perms:
                    context.reply(context.localize(
                        "Sorry, you can't execute this command cause I lack following permissions: {}").format(
                        ', '.join(missing_perms)))

        return wrapper

    return decorator
