import telegram

import octobot
from octobot.classes.catalog import CatalogPhoto
from octobot.handlers import CommandHandler, InlineButtonHandler
from octobot.localization import localizable
from settings import Settings
info = octobot.PluginInfo("Test plugin")

if Settings.production:
    raise octobot.DontLoadPlugin

@CommandHandler(command="ptest", description="Permissions test")
@octobot.permissions(can_restrict_members=True)
@octobot.my_permissions(can_delete_messages=True)
def test_perm(bot, context):
    context.reply("Hello world!",
                  reply_markup=telegram.InlineKeyboardMarkup([
                      [telegram.InlineKeyboardButton(callback_data="test:", text="Change text")]
                  ])
                  )

@CommandHandler(command="exception", description="Test exception")
def test_exception(*_):
    1/0

@CommandHandler(command="inline_exc", description="Test exception in inline buttons")
def test_inline_exception_c(bot, context):
    context.reply("Hello world! " + context.query,
                  reply_markup=telegram.InlineKeyboardMarkup([
                      [telegram.InlineKeyboardButton(callback_data="inlineexc:", text="Exception")]
                  ])
                  )

@InlineButtonHandler("inlineexc")
def test_inline_exception(*_):
    1/0


@CommandHandler(command="test", description="Test")
def test(bot, context):
    context.reply("Hello world! " + context.query,
                  reply_markup=telegram.InlineKeyboardMarkup([
                      [telegram.InlineKeyboardButton(callback_data="test:", text="Change text")]
                  ])
                  )


@CommandHandler(command="imgtest", description="Test image handling")
def imgtest(bot, context):
    context.reply("Test!", photo_url="https://picsum.photos/seed/test/200/200",
                  reply_markup=telegram.InlineKeyboardMarkup([
                      [telegram.InlineKeyboardButton(callback_data="imgtest:", text="Change image and text")]
                  ]))


@InlineButtonHandler(prefix="imgtest:")
def imgtest_button(bot, context):
    context.edit("Test! Test!", photo_url="https://picsum.photos/seed/test2/200/200")
    context.reply("Changed image!")


@InlineButtonHandler(prefix="test:")
def test_button(bot, context):
    context.edit("Test! Test!")
    context.reply("Changed text!")


CATALOG_MAX = 10


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


@CommandHandler(command="helloworld", description=localizable("Hello, World!"))
def hello_world(bot, ctx):
    ctx.reply(ctx.localize("This is a test"))


@CommandHandler(command="pmtest")
def pmtest(bot, ctx: octobot.Context):
    ctx.reply("Check your PMs!")
    ctx.reply("Test", to_pm=True)


