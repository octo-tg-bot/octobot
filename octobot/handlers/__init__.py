from octobot.handlers.basehandler import BaseHandler
from octobot.handlers.choseninlineresulthandle import ChosenInlineResultHandler
from octobot.handlers.commandhandle import CommandHandler
from octobot.handlers.buttonhandle import InlineButtonHandler
from octobot.handlers.inlinequeryhandle import InlineQueryHandler
from octobot.handlers.messagehandler import MessageHandler


class ExceptionHandler:
    def handle_exception(self, bot, context, exception):
        return
