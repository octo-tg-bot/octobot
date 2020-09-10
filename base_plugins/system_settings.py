import json
import traceback

import octobot
from settings import Settings

inf = octobot.PluginInfo("Settings Ctl",
                         handler_kwargs={
                             "CommandHandler": {
                                 "prefix": "sys!",
                                 "hidden": True,
                                 "inline_support": False
                             }
                         },
                         reply_kwargs={"editable": False})


def get_nested(data, *args):
    if args and data:
        element = args[0]
        if element:
            value = data.get(element)
            return value if len(args) == 1 else get_nested(value, *args[1:])


@octobot.CommandHandler("settings_get", required_args=1)
@octobot.permissions("is_bot_owner")
def settings_get(bot, ctx):
    value = ctx.query.split(", ")
    ctx.reply(f"{value}: {get_nested(Settings, *value)}")


@octobot.CommandHandler("settings_set", required_args=2)
@octobot.permissions("is_bot_owner")
def settings_set(bot, ctx):
    args = ctx.query.split(" ")
    key = args[0]
    value = " ".join(args[1:])
    try:
        getattr(Settings, key)
    except KeyError:
        ctx.reply(f"Unknown var {key}")
        return
    try:
        value = json.loads(value)
    except json.JSONDecodeError as e:
        ctx.reply(f"Error while parsing value: {e}")
        return
    Settings[key] = value
    ctx.reply("Value set")


@octobot.CommandHandler("settings_reload")
@octobot.permissions("is_bot_owner")
def settings_reload(bot, ctx):
    try:
        Settings.reload_settings()
    except Exception as e:
        ctx.reply(f"Error:\n{traceback.format_exc()}")
    else:
        ctx.reply("Settings reloaded")

@octobot.CommandHandler("settings_save")
@octobot.permissions("is_bot_owner")
def settings_save(bot, ctx):
    try:
        Settings.save_settings_to_disk()
    except Exception as e:
        ctx.reply(f"Error:\n{traceback.format_exc()}")
    else:
        ctx.reply("Settings saved")