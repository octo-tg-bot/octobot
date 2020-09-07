from octobot.handlers import InlineButtonHandler
import telegram

@InlineButtonHandler("nothing:")
def nothing_reply(bot, ctx):
    ctx.reply("🦀")

@InlineButtonHandler("invalid:")
def unknown_reply(bot, ctx):
    ctx.reply(ctx.localize("I can't understand what this inline button does. The keyboard here is probably outdated."))
    # ctx.edit(reply_markup=telegram.InlineKeyboardMarkup([]))

@InlineButtonHandler("smartass:")
def smartass_reply(bot, ctx):
    ctx.reply(ctx.localize("I am sorry Dave, I am afraid I cant do that."))
