import logging
import re

import telegram

import octobot
from octobot.__system.database import DatabaseNotAvailable
import sys

logger = logging.getLogger("Exceptions")


class ExceptionHandler:
    def handle_exception(self, bot, context, exception):
        return


class UnknownUpdate(ValueError):
    """
    This exception gets raised during update handle if Context failed to determine update
    """
    pass


class LoaderCommand(Exception):
    """
    Base exception for OctoBot handler commands
    """
    pass


class PassExceptionToDebugger(LoaderCommand):
    """
    Exception for raising exception from octobot itself, to pass it to debugger, for example.

    :param exception_to_pass: Exception to raise
    :type exception_to_pass: Exception
    """

    def __init__(self, exception_to_pass):
        self.exception = exception_to_pass


class StopHandling(LoaderCommand):
    """
    OctoBot stops trying to use other handles if that exception was raised
    """
    pass


class CatalogBaseException(IndexError):
    """Base exception for catalog commands"""
    pass


class CatalogCantGoDeeper(CatalogBaseException):
    """Raise this exception is maximum number of results is reached"""
    pass


class CatalogCantGoBackwards(CatalogBaseException):
    """Raise this exception if it's impossible to go backwards"""
    pass


class CatalogNotFound(CatalogBaseException):
    """Raise this exception if no results were found"""
    pass


class DontLoadPlugin(RuntimeError):
    """Raise this exception if you dont want plugin to continue loading"""
    pass


class Halt(LoaderCommand):
    """Raise this exception to make bot stop handling any further updates and quit"""
    pass


async def handle_exception(bot: "octobot.OctoBot", context, e, notify=True):
    logger.info("handling %s", e)
    if isinstance(e, LoaderCommand) or isinstance(e, CatalogBaseException):
        raise e
    elif isinstance(e, telegram.error.Forbidden):
        if "bot was kicked" or "bot was blocked" in e.message:
            return
    elif isinstance(e, telegram.error.BadRequest) and e.message in ("Cancelled by new editmessagemedia request",
                                                                    "Query is too old and response timeout expired or query id is invalid"):
        return
    elif isinstance(e, telegram.error.BadRequest) and e.message == "Have no rights to send a message":
        chat = context.update.effective_chat
        if chat is None:
            # Shouldn't happen, but check just in case
            raise e
        logger.info(
            "Chat %s probably restricted or kicked bot. Attempting to leave...", chat.id)
        try:
            await chat.leave()
        except telegram.error.TelegramError:
            pass
        return
    elif isinstance(e, telegram.error.TimedOut):
        return
    else:
        message = context.localize(
            "🐞 Failed to execute command due to unknown error.")
        err_handlers_msgs = [message]
        err_handlers_markup = []
        for err_handler in bot.error_handlers:
            err_handler: ExceptionHandler
            values = await err_handler.handle_exception(bot, context, e)
            if values is None:
                continue
            elif len(values) == 2:
                text, markup = values
                err_handlers_markup.append(markup)
            else:
                text = values
            err_handlers_msgs.append(text)
        if notify:
            if len(err_handlers_markup) == 0:
                err_handlers_markup = None
            else:
                err_handlers_markup = telegram.InlineKeyboardMarkup(
                    err_handlers_markup)
            message = "\n".join(err_handlers_msgs)
            logger.debug("message: %s, ctx: %s", message, context)
            if isinstance(context, octobot.MessageContext) or isinstance(context, octobot.InlineQueryContext):
                await context.reply(message, parse_mode="HTML",
                                    title=context.localize("Error occured"),
                                    reply_markup=err_handlers_markup)
            elif isinstance(context, octobot.CallbackContext):
                message = re.sub(r"<[^>]*>", '', message)
                await context.update.callback_query.answer(
                    message[0], show_alert=True)
