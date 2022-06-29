import json
import telegram

import octobot
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


@octobot.helpers.CatalogHelper(command="catalogtest", description="Test CatalogHandler")
async def test_catalog(bot, context, slice, query):
    res = []
    plugin.logger.debug("slice: %s", slice)
    for i in range(slice.start, slice.stop):
        res.append(octobot.catalogs.CatalogKeyPhoto(text=f"<b>{query}</b> <i>{i}</i>",
                                                    title=f"Title for {query}",
                                                    description=f"Description for {query}",
                                                    parse_mode="HTML",
                                                    reply_markup=telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(
                                                        url="https://example.com", text="Test")]]),
                                                    photo=[octobot.catalogs.CatalogPhoto(
                                                        url=f"https://picsum.photos/seed/{query}{i}/200/300",
                                                    )]))
    return octobot.catalogs.CatalogResult(res, current_index=slice.stop, next_offset=slice.stop,
                                          previous_offset=None if slice.start == 0 else slice.start - 1, total=150)
