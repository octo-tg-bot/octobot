import datetime
import os
import unittest, unittest.mock
import telegram
import octobot
import plugins.test

USER = telegram.User(is_bot=False, first_name="Unittest 'human'", id=1)
CHAT = telegram.Chat(1, title=USER.name, type="private")

class TestOctoBot(unittest.TestCase):
    @unittest.mock.patch("octobot.context.Context.reply")
    def test_cmdHandle(self, reply):
        os.environ["ob_production"] = 'false'
        bot = octobot.OctoBot(["plugins.test"])
        update = telegram.Update(update_id=0,
                                 message=telegram.Message(
                                     message_id=0,
                                     from_user=USER,
                                     chat=CHAT,
                                     text="/test hi",
                                     date=datetime.datetime.now()
                                 ))
        bot.handle_update(bot, update)
        reply.assert_called_with("Hello world! hi", reply_markup=telegram.InlineKeyboardMarkup([
                                      [telegram.InlineKeyboardButton(callback_data="test:", text="Change text")]
                                  ]))


if __name__ == '__main__':
    unittest.main()
