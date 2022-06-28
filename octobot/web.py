from fastapi import FastAPI
import octobot
# @staticmethod
# def create_context(update, bot, message=None):
#     if message is None and update.message is not None:
#         message = update.message

#     if update.inline_query:
#         return InlineQueryContext(update, bot, message)
#     elif update.callback_query:
#         return CallbackContext(update, bot, message)
#     elif message:
#         return MessageContext(update, bot, message)
#     elif update.edited_message:
#         return EditedMessageContext(update, bot, message)
#     elif update.chosen_inline_result:
#         return ChosenInlineResultContext(update, bot, message)
#     else:
#         raise octobot.exceptions.UnknownUpdate(
#             "Failed to determine update type for update %s", update.to_dict())


def create_webapp(bot: octobot.OctoBot):

    app = FastAPI()

    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    return app
