import html
import json
import subprocess
import traceback

import telegram
from telegram.error import TimedOut

import octobot
from settings import Settings

inf = octobot.PluginInfo("Evaluation",
                         handler_kwargs={
                             "CommandHandler": {
                                 "prefix": "sys!",
                                 "hidden": True,
                                 "inline_support": False
                             }
                         },
                         reply_kwargs={"editable": False})



@octobot.CommandHandler("eval")
@octobot.permissions("is_bot_owner")
def evaluate(bot, ctx):
    try:
        res = eval(ctx.query)
    except Exception as e:
        ctx.reply(f"Exception: {e} ({type(e)})")
    else:
        ctx.reply(f"Result: {res}")
