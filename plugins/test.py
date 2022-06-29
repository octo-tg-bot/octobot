import json
import telegram

import octobot
from octobot.classes.catalog import CatalogPhoto
from octobot.filters import CommandFilter
from octobot.localization import localizable
from octobot import settings
plugin = octobot.PluginInfo("Test plugin")

if settings.production:
    raise octobot.DontLoadPlugin


@CommandFilter(command="exception", description="Test exception")
def test_exception(*_):
    1/0


@CommandFilter(command="inline_exc", description="Test exception in inline buttons")
def test_inline_exception_c(bot, context):
    context.reply("Hello world! " + context.query,
                  reply_markup=telegram.InlineKeyboardMarkup([
                      [telegram.InlineKeyboardButton(
                          callback_data="inlineexc:", text="Exception")]
                  ])
                  )


@CommandFilter(command="helloworld", description=localizable("Hello, World!"))
async def hello_world(bot, ctx):
    await ctx.reply(ctx.localize("This is a test"))


@CommandFilter(command="wchat", description=localizable("Write data into chat db."), required_args=2)
async def wchat(bot, ctx):
    ctx.chat_db[ctx.args[0]] = ctx.args[1]
    await ctx.reply(ctx.localize("Written"))


@CommandFilter(command="rchat", description=localizable("Write data into chat db."))
async def rchat(bot, ctx):
    await ctx.reply(json.dumps(ctx.chat_db))


@CommandFilter(command="pmtest")
def pmtest(bot, ctx: octobot.Context):
    ctx.reply("Check your PMs!")
    ctx.reply("Test", to_pm=True)
