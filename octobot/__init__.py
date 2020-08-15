from octobot.exceptions import *
from octobot.database import Database
from octobot.classes import *
from octobot.handlers import *
from octobot.loader import OctoBot, PluginStates
from octobot.localization import localizable
from octobot import catalogs
from octobot.permissions import permissions, my_permissions, reset_cache
from octobot.permissions import create_db_entry_name as _perm_db_entry

def supergroup_only(function):
    def wrapper(bot, context):
        if context.update_type in [UpdateType.button_press, UpdateType.message] and context.chat.type == "supergroup":
            function(bot, context)
        else:
            context.reply(context.localize("This command can be used only in supergroups."))
    return wrapper

