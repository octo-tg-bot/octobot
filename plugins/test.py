from octobot.handlers import CommandHandler, InlineButtonHandler
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
def imgtest_button(bot, context):
    context.edit("Test! Test!")
    context.reply("Changed text!")