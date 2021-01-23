# The MIT License (MIT)
# Copyright (c) 2021 OctoNezd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

import datetime
import html

import pytz

import octobot
PLUGINS = {}
def create_plugins_list(bot: octobot.OctoBot):
    PLUGINS.clear()
    for plugin, info in bot.plugins.items():
        if not plugin.split(".")[0] == "base_plugins" and info.state in (octobot.PluginStates.loaded, octobot.PluginStates.warning):
            PLUGINS[plugin] = info.name
    plugin_inf.logger.info("Created plugins list: %s",PLUGINS)

plugin_inf = octobot.PluginInfo(octobot.localizable("Plugin management"), after_load=create_plugins_list)
if octobot.Database.redis is None:
    plugin_inf.state = octobot.PluginStates.disabled
    plugin_inf.state_description = "API Key is not set. Get it @ https://free.currencyconverterapi.com/"

def get_disabled_plugins(chat:int):
    return octobot.Database.redis.smembers(f"plugins_disabled{chat}")

@octobot.CommandHandler(command="list_disabled",
                        description=octobot.localizable("Lists disabled plugins in this chat"))
@octobot.supergroup_only
def list_disabled(bot: octobot.OctoBot, ctx: octobot.Context):
    disabled = get_disabled_plugins(ctx.chat.id)
    if len(disabled) == 0:
        return ctx.reply(ctx.localize("No plugins are disabled in this chat"))
    print(disabled)
    message = ctx.localize("Disabled plugins:")
    for plugin in disabled:
        message += f"\n- <code>{plugin.decode()}</code>"
    ctx.reply(message, parse_mode="HTML")

def send_disableable_plugins_reply(ctx):
    disableable = []
    for plugin, plugin_desc in PLUGINS.items():
        disableable.append(f"<code>{html.escape(plugin)}</code> - {html.escape(ctx.localize(plugin_desc))}")
    disableable = '- ' + "\n- ".join(disableable)
    return ctx.reply(
        ctx.localize("You hadn't specified plugin to disable/enable. Following plugins can be disabled:\n") + \
        disableable, parse_mode="HTML")

@octobot.CommandHandler(command="disable_plugin")
@octobot.supergroup_only
@octobot.permissions(can_change_info=True)
def disable_plugin(bot: octobot.OctoBot, ctx: octobot.Context):
    if len(ctx.args) == 0:
        send_disableable_plugins_reply(ctx)
    elif ctx.query == "*":
        octobot.Database.redis.sadd(f"plugins_disabled{ctx.chat.id}", *PLUGINS.keys())
        return ctx.reply(ctx.localize("All disable-able plugins were disabled."))
    elif ctx.query in PLUGINS:
        octobot.Database.redis.sadd(f"plugins_disabled{ctx.chat.id}", ctx.query)
        return ctx.reply(ctx.localize("{plugin_desc} (<code>{plugin_id}</code>) was disabled.").format(
            plugin_desc=PLUGINS[ctx.query],
            plugin_id=ctx.query
        ), parse_mode="HTML")
    else:
        return ctx.reply(ctx.localize("Unknown plugin: ") + ctx.query)

@octobot.CommandHandler(command="enable_plugin")
@octobot.supergroup_only
@octobot.permissions(can_change_info=True)
def enable_plugin(bot: octobot.OctoBot, ctx: octobot.Context):
    if len(ctx.args) == 0:
        send_disableable_plugins_reply(ctx)
    elif ctx.query == "*":
        octobot.Database.redis.delete(f"plugins_disabled{ctx.chat.id}")
        return ctx.reply(ctx.localize("All disable-able plugins were enabled."))
    elif ctx.query in PLUGINS:
        octobot.Database.redis.srem(f"plugins_disabled{ctx.chat.id}", ctx.query)
        return ctx.reply(ctx.localize("{plugin_desc} (<code>{plugin_id}</code>) was enabled.").format(
            plugin_desc=PLUGINS[ctx.query],
            plugin_id=ctx.query
        ), parse_mode="HTML")
    else:
        return ctx.reply(ctx.localize("Unknown plugin: ") + ctx.query)