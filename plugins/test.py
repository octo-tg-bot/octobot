import telegram

import octobot
from octobot.classes.catalog import CatalogPhoto
from octobot.filters import CommandFilter
from octobot.localization import localizable
from octobot import settings
info = octobot.PluginInfo("Test plugin")

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


CATALOG_MAX = 50


@octobot.catalogs.CatalogHandler(command="catalogtest", description="Test CatalogHandler")
def test_catalog(query, index, max_amount, bot, context):
    res = []
    index = int(index)
    if index < 0:
        raise octobot.CatalogCantGoBackwards
    if index >= CATALOG_MAX:
        raise octobot.CatalogCantGoDeeper
    if max_amount > CATALOG_MAX:
        max_amount = CATALOG_MAX
    for i in range(0, max_amount):
        res.append(octobot.CatalogKeyPhoto(text=f"<b>{query}</b> <i>{i + index}</i>",
                                           title=f"Title for {query}",
                                           description=f"Description for {query}",
                                           parse_mode="HTML",
                                           reply_markup=telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(
                                               url="https://example.com", text="Test")]]),
                                           photo=[CatalogPhoto(
                                               url=f"https://picsum.photos/seed/{query}{i + index}/200/300",
                                           )]))
    return octobot.Catalog(res, current_index=index + 1, next_offset=index + max_amount,
                           previous_offset=index - max_amount, max_count=CATALOG_MAX, photo_primary=True)


@octobot.catalogs.CatalogHandler(command="catalogtesta", description="Test CatalogHandler with Articles")
def test_catalogarticle(query, index, max_amount, bot, context):
    res = []
    index = int(index)
    if index < 0:
        raise octobot.CatalogCantGoBackwards
    if index >= CATALOG_MAX:
        raise octobot.CatalogCantGoDeeper
    if max_amount > CATALOG_MAX:
        max_amount = CATALOG_MAX
    if query == "nothing":
        raise octobot.CatalogNotFound
    for i in range(0, max_amount):
        res.append(octobot.CatalogKeyArticle(text=f"{query} {i + index}",
                                             title=f"Title for {query}",
                                             description=f"Description for {query}",
                                             photo=[CatalogPhoto(
                                                 url=f"https://picsum.photos/seed/{query}{i + index}/1000/1000",
                                                 width=1000,
                                                 height=1000)]))
    return octobot.Catalog(res, max_count=CATALOG_MAX, current_index=index, next_offset=index + max_amount,
                           previous_offset=index - max_amount)


@CommandFilter(command="helloworld", description=localizable("Hello, World!"))
async def hello_world(bot, ctx):
    await ctx.reply(ctx.localize("This is a test"))


@CommandFilter(command="pmtest")
def pmtest(bot, ctx: octobot.Context):
    ctx.reply("Check your PMs!")
    ctx.reply("Test", to_pm=True)
