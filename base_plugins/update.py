import html
import json
import subprocess
import traceback

import telegram

import octobot
from settings import Settings

inf = octobot.PluginInfo("Bot update",
                         handler_kwargs={
                             "CommandHandler": {
                                 "prefix": "sys!",
                                 "hidden": True,
                                 "inline_support": False
                             }
                         },
                         reply_kwargs={"editable": False})


def reload(bot: octobot.OctoBot, ctx):
    msg: telegram.Message = ctx.reply("Reloading...")
    for plugin in bot.discover_plugins()["load_order"]:
        res = bot.load_plugin(plugin)
        msg = ctx.edit(msg.text + f"\n{plugin} - {res}")
    bot.update_handlers()
    ctx.edit(msg.text + f"\nRELOADED")


@octobot.CommandHandler("reload")
@octobot.permissions("is_bot_owner")
def reload_cmd(bot, ctx):
    reload(bot, ctx)


@octobot.CommandHandler("update")
@octobot.permissions("is_bot_owner")
def update(bot, ctx):
    update_type = "soft"
    if len(ctx.args) > 0:
        update_type = ctx.args[1]
    update_type = update_type.lower()
    if update_type not in ["soft", "hard"]:
        ctx.reply(f"unknown update type {update_type}")
        return
    pull_res = subprocess.check_output("git pull", shell=True)
    ctx.reply(f"<code>{html.escape(pull_res.decode())}</code>", parse_mode="HTML")
    if update_type == "soft":
        reload(bot, ctx)
    else:
        raise SystemExit
