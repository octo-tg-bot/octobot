import logging
import re

import telegram

import octobot
from octobot.database import DatabaseNotAvailable
from octobot.handlers import ExceptionHandler

logger = logging.getLogger("Exceptions")


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


def handle_exception(bot: "octobot.OctoBot", context, e, notify=True):
    logger.info("handling %s", e)
    if isinstance(e, DatabaseNotAvailable):
        if notify:
            if context.update_type == octobot.UpdateType.message or context.update_type == octobot.UpdateType.inline_query:
                context.reply(context.localize("Failed to execute command due to database problems. Please try later"))
            elif context.update_type == octobot.UpdateType.button_press:
                context.edit(context.localize("Failed to execute command due to database problems. Please try later"))
    elif isinstance(e, LoaderCommand) or isinstance(e, CatalogBaseException):
        raise e
    elif isinstance(e, telegram.error.Unauthorized):
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
        logger.info("Chat %s probably restricted or kicked bot. Attempting to leave...", chat.id)
        try:
            chat.leave()
        except telegram.error.TelegramError:
            pass
        return
    else:
        logger.error("Exception got thrown somewhere", exc_info=True)
        message = context.localize("🐞 Failed to execute command due to unknown error.")
        err_handlers_msgs = [message]
        err_handlers_markup = []
        for err_handler in bot.error_handlers:
            err_handler: ExceptionHandler
            values = err_handler.handle_exception(bot, context, e)
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
                err_handlers_markup = telegram.InlineKeyboardMarkup(err_handlers_markup)
            message = "\n".join(err_handlers_msgs)
            logger.debug(message)
            if context.update_type == octobot.UpdateType.message or context.update_type == octobot.UpdateType.inline_query:
                context.reply(message, parse_mode="HTML", reply_markup=err_handlers_markup)
            elif context.update_type == octobot.UpdateType.button_press:
                message = re.sub(r"<[^>]*>", '', message)
                context.update.callback_query.answer(message, show_alert=True)
                # context.edit(message)
