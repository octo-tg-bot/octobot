import os
import subprocess
import contextvars

from .__system import settings
from .__system import database
from octobot.localization import localizable
from octobot.classes import UpdateType, PluginInfo, Context, CallbackContext, MessageContext, ChosenInlineResultContext, \
    EditedMessageContext, InlineQueryContext
from octobot import filters, catalogs, exceptions
from octobot.misc import Suggestion, PluginStates
from octobot.loader import OctoBot

is_docker = os.path.exists("/.dockerenv")
current_context = contextvars.ContextVar('Current context data.')


try:
    if not is_docker:
        __version__ = subprocess.check_output('git describe --dirty',
                                              shell=True).decode('utf-8').replace("\n", "")
    elif os.path.exists(".git-version"):
        __version__ = open(".git-version").read().replace("\n", "")
except Exception:
    __version__ = "Unknown"
