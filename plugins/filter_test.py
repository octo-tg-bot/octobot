import octobot
from settings import Settings
info = octobot.PluginInfo("Filter test plugin")

if Settings.production:
    raise octobot.DontLoadPlugin


@octobot.CommandFilter("ftest")
def commandfilter(bot, ctx):
    ctx.reply("Command filter test")
