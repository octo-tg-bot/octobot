import telegram

from octobot import CatalogKeyPhoto, Catalog, CatalogCantGoDeeper, CatalogKeyArticle, CatalogNotFound, \
    CatalogCantGoBackwards, catalogs
from octobot.classes.catalog import CatalogPhoto
from octobot.handlers import CommandHandler, InlineButtonHandler
from octobot.localization import localizable


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


@catalogs.CatalogHandler(command="catalogtest", description="Test CatalogHandler")
def test_catalog(query, index, max_amount, bot, context):
    res = []
    index = int(index)
    if index < 0:
        raise CatalogCantGoBackwards
    if index >= CATALOG_MAX:
        raise CatalogCantGoDeeper
    if max_amount > CATALOG_MAX:
        max_amount = CATALOG_MAX
    for i in range(0, max_amount):
        res.append(CatalogKeyPhoto(text=f"<b>{query}</b> <i>{i + index}</i>",
                                   title=f"Title for {query}",
                                   description=f"Description for {query}",
                                   parse_mode="HTML",
                                   photo=[CatalogPhoto(url=f"https://picsum.photos/seed/{query}{i + index}/200/200",
                                                       width=200,
                                                       height=200)]))
    return Catalog(res, CATALOG_MAX, current_index=index+1, next_offset=index+max_amount, previous_offset=index-max_amount)


@catalogs.CatalogHandler(command="catalogtesta", description="Test CatalogHandler with Articles")
def test_catalogarticle(query, index, max_amount, bot, context):
    res = []
    index = int(index)
    if index < 0:
        raise CatalogCantGoBackwards
    if index >= CATALOG_MAX:
        raise CatalogCantGoDeeper
    if max_amount > CATALOG_MAX:
        max_amount = CATALOG_MAX
    if query == "nothing":
        raise CatalogNotFound
    for i in range(0, max_amount):
        res.append(CatalogKeyArticle(text=f"{query} {i + index}",
                                     title=f"Title for {query}",
                                     description=f"Description for {query}",
                                     photo=[CatalogPhoto(url=f"https://picsum.photos/seed/{query}{i + index}/200/200",
                                                         width=200,
                                                         height=200)]))
    return Catalog(res, CATALOG_MAX, current_index=index, next_offset=index+max_amount, previous_offset=index-max_amount)



@CommandHandler(command="helloworld", description=localizable("Hello, World!"))
def hello_world(bot, ctx):
    ctx.reply(ctx.localize("This is a test"))