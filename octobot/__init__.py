import os
import subprocess

from octobot.database import Database
from octobot.localization import localizable
from octobot.enums import PluginStates
from octobot.exceptions import *
from octobot.classes import *
from octobot.filters import ContextFilter, CommandFilter, PermissionFilter
from octobot.handlers import CommandHandler, ExceptionHandler, MessageHandler, InlineButtonHandler, InlineQueryHandler, \
    ChosenInlineResultHandler
from octobot.loader import OctoBot
from octobot import catalogs
from octobot.permissions import permissions, my_permissions, reset_cache, not_admin
from octobot.permissions import check_perms as check_permissions
from octobot.permissions import create_db_entry_name as _perm_db_entry
from octobot.dataclass import Suggestion

is_docker = os.path.exists("/.dockerenv")


def supergroup_only(function):
    """
    Decorator that checks if command is issued in supergroup. Disables inline mode for command.
    """

    def wrapper(bot, context):
        if (isinstance(context, octobot.CallbackContext) or type(context) == octobot.MessageContext) and context.chat.type == "supergroup":
            function(bot, context)
        else:
            context.reply(context.localize(
                "This command can be used only in supergroups."))

    return wrapper


try:
    if not is_docker:
        __version__ = subprocess.check_output('git describe --dirty',
                                              shell=True).decode('utf-8').replace("\n", "")
    elif os.path.exists(".git-version"):
        __version__ = open(".git-version").read().replace("\n", "")
except Exception:
    __version__ = "Unknown"
