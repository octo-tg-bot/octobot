from .basefilters import BaseFilter
from ..permissions import check_perms, permissions_locale


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
            res, missing_perms = check_perms(
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
            res, missing_perms = check_perms(
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
                res, missing_perms = check_perms(
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
