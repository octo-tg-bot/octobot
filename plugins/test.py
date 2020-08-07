from octobot.handlers import CommandHandler, InlineButtonHandler, CatalogHandler
from octobot import CatalogKey, Catalog, CatalogCantGoDeeper
import telegram


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


CATALOG_MAX = 10


@CatalogHandler(command="catalogtest", description="Test CatalogHandler")
def test_catalog(query, index, max_amount, bot, context):
    res = []

    if index >= CATALOG_MAX:
        raise CatalogCantGoDeeper
    if max_amount > CATALOG_MAX:
        max_amount = CATALOG_MAX
    for i in range(0, max_amount):
        res.append(CatalogKey(text=f"{query} {i + index}",
                              photo_url=f"https://picsum.photos/seed/{query}{i + index}/200/200"))
    return Catalog(res, 10)
