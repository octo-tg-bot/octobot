from octobot.handlers import InlineButtonHandler

@InlineButtonHandler("nothing:")
def nothing_reply(bot, ctx):
    ctx.reply("🦀")