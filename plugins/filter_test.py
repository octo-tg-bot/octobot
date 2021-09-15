import octobot
import telegram
from settings import Settings
info = octobot.PluginInfo("Filter test plugin")

if Settings.production:
    raise octobot.DontLoadPlugin


@octobot.CommandFilter("ftest")
def commandfilter(bot, ctx):
    def reply_inline(bot, ctx):
        ctx.edit("Edited text!")
        ctx.reply("OK!")
    ctx.reply("Command filter test", reply_markup=telegram.InlineKeyboardMarkup.from_button(
        telegram.InlineKeyboardButton("Test button", callback_data=octobot.Callback(reply_inline)))
    )


@octobot.CommandFilter("fptest")
@octobot.PermissionFilter(who="bot", permissions="is_admin")
def permission_filter(bot, ctx):
    ctx.reply("Bot has is_admin")


@octobot.PermissionFilter(who="bot", permissions="is_admin")
@octobot.CommandFilter("fptest2")
def permission_filter2(bot, ctx):
    ctx.reply("Bot has is_admin")


@octobot.PermissionFilter(who="caller", permissions="is_admin")
@octobot.CommandFilter("fpcaller")
def permission_filter_caller(bot, ctx):
    ctx.reply("You have is_admin")


@octobot.PermissionFilter(who="replied_user", permissions="is_admin")
@octobot.CommandFilter("fpreplied")
def permission_filter_replied(bot, ctx):
    ctx.reply("This user doesn't have is_admin")
