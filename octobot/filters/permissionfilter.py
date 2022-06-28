from .basefilters import BaseFilter
import logging
import typing
import telegram
from octobot import database, localizable


permissions_locale = {
    "is_bot_owner": localizable("bot owner. Who the fu - Who is - What - I should kick your fucking ass, "
                                "who is this?"),
    "can_change_info": localizable("change chat info"),
    "is_admin": localizable("chat admin"),
    "can_delete_messages": localizable("delete messages"),
    "can_restrict_members": localizable("restrict members"),
    "can_pin_messages": localizable("pin messages"),
    "can_promote_members": localizable("promote members"),
    "can_manage_chat": localizable("manage chat"),
    "can_manage_voice_chats": localizable("manage voice chats")
}
logger = logging.getLogger("permissions")


def create_db_entry_name(chat: typing.Union[telegram.Chat, int]):
    if isinstance(chat, telegram.Chat):
        chat = chat.id
    return f"admcache:{chat}"


def reset_cache(chat: typing.Union[telegram.Chat, int]):
    return database.redis.delete(create_db_entry_name(chat))


def check_permissions(chat: typing.Union[telegram.Chat, int], user: typing.Union[telegram.User, int],
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
        if Settings.owner == user_id:
            permissions_to_check.remove("is_bot_owner")
        return Settings.owner == user_id, permissions_to_check
    if not str(chat_id).startswith("-100"):
        return True, []
    adm_list = None
    if database.redis is not None and database.redis.exists(db_entry) == 1:
        db_res = database.redis.get(db_entry)
        if db_res is not None:  # fix some weird bug that i have 0 idea how it happens
            adm_list = json.loads(db_res.decode())
    if adm_list is None:
        if bot is None:
            adm_list_t = chat.get_administrators()
        else:
            adm_list_t = bot.get_chat_administrators(chat_id=chat_id)
        adm_list = []
        for admin in adm_list_t:
            adm_list.append(admin.to_dict())
        if database.redis is not None:
            database.redis.set(db_entry, json.dumps(adm_list))
            database.redis.expire(db_entry, 240)
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


class PermissionFilter(BaseFilter):
    def __init__(self, who, permissions):
        if who not in ["replied_user", "caller", "bot"]:
            raise ValueError(
                "who must be one of the following: replied_user, caller, bot")
        self.who = who
        if who == "bot":
            self._filterWeight = 2
        elif who == "replied_user":
            self._filterWeight = 1
        self.permissions = permissions
        if isinstance(permissions, str):
            self.permissions = [permissions]

    def validate(self, bot, context):
        if context.chat is None:
            return False
        if self.who == "bot":
            res, missing_perms = check_permissions(
                context.chat, bot.me, self.permissions.copy())
            missing_perms_localized = [context.localize(
                permissions_locale[permission]) for permission in missing_perms]
            if res:
                return True
            elif "is_admin" not in missing_perms:
                context.reply(context.localize(
                    "Sorry, you can't execute this command cause I lack following permissions: {}").format(
                    ', '.join(missing_perms_localized)))
            return False
        elif self.who == "caller":
            res, missing_perms = check_permissions(
                context.chat, context.user, self.permissions.copy())
            missing_perms_localized = [context.localize(
                permissions_locale[permission]) for permission in missing_perms]
            if res:
                return True
            else:
                context.reply(context.localize(
                    "Sorry, you can't execute this command cause you lack following permissions: {}").format(
                    ', '.join(missing_perms_localized)))
            return False
        elif self.who == "replied_user":
            if context.update.message.reply_to_message is not None:
                res, missing_perms = check_permissions(
                    context.chat, context.update.message.reply_to_message.from_user, self.permissions.copy())
                perms_localized = [context.localize(
                    permissions_locale[permission]) for permission in self.permissions]
                if not res:
                    return True
                else:
                    context.reply(context.localize(
                        "Sorry, you can't execute this command cause this user has following permissions: {}").format(
                        ', '.join(perms_localized)))
                    return False
            else:
                return True
