import telegram

import octobot
from octobot.classes.catalog import CatalogPhoto
from octobot.handlers import CommandHandler, InlineButtonHandler
from octobot.localization import localizable


@CommandHandler(command="ptest", description="Permissions test")
@octobot.permissions(can_restrict_members=True)
@octobot.my_permissions(can_delete_messages=True)
def test_perm(bot, context):
    context.reply("Hello world!",
                  reply_markup=telegram.InlineKeyboardMarkup([
                      [telegram.InlineKeyboardButton(callback_data="test:", text="Change text")]
                  ])
                  )


@CommandHandler(command="test", description="Test")
def test(bot, context):
    context.reply("Hello world!",
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
                                               url=f"https://picsum.photos/seed/{query}{i + index}/200/200",
                                               width=200,
                                               height=200)]))
    return octobot.Catalog(res, CATALOG_MAX, current_index=index + 1, next_offset=index + max_amount,
                               previous_offset=index - max_amount)

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
                                                 url=f"https://picsum.photos/seed/{query}{i + index}/200/200",
                                                 width=200,
                                                 height=200)]))
    return octobot.Catalog(res, CATALOG_MAX, current_index=index, next_offset=index + max_amount,
                           previous_offset=index - max_amount)

@CommandHandler(command="helloworld", description=localizable("Hello, World!"))
def hello_world(bot, ctx):
    ctx.reply(ctx.localize("This is a test"))

info = octobot.PluginInfo("Test plugin")
