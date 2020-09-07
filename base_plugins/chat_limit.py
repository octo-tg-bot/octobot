import telegram

import octobot
from settings import Settings

if Settings.allowed_chats == []:
    raise octobot.DontLoadPlugin("All chats are allowed")


@octobot.MessageHandler(priority=-1)
def check_allowed(bot, ctx):
    if ctx.chat.type == "supergroup" and ctx.chat.id not in Settings.allowed_chats:
        try:
            ctx.reply(Settings.disallowed_chat_reason)
            ctx.chat.leave()
        except telegram.error.Unauthorized:
            pass
        finally:
            raise octobot.StopHandling
