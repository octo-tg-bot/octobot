import octobot
import logging

from settings import Settings

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


class DatabaseNotAvailable(ConnectionError):
    """Gets raised if database cant be accessed"""
    pass


class DontLoadPlugin(RuntimeError):
    """Raise this exception if you dont want plugin to continue loading"""
    pass


class Halt(LoaderCommand):
    """Raise this exception to make bot stop handling any further updates and quit"""
    pass


def handle_exception(bot, context, e, notify=True):
    if isinstance(e, DatabaseNotAvailable):
        if notify:
            if context.update_type == octobot.UpdateType.message or context.update_type == octobot.UpdateType.inline_query:
                context.reply(context.localize("Failed to execute command due to database problems. Please try later"))
            elif context.update_type == octobot.UpdateType.button_press:
                context.edit(context.localize("Failed to execute command due to database problems. Please try later"))
    elif isinstance(e, LoaderCommand) or isinstance(e, CatalogBaseException):
        raise e
    else:
        logger.error("Exception got thrown somewhere", exc_info=True)
        if notify:
            message = context.localize("🐞 Failed to execute command due to unknown error.")
            report_type = Settings.exceptions["report_type"]
            if report_type == "describe":
                message += "\n" + context.localize("Error description: {error}").format(error=str(e))
            if context.update_type == octobot.UpdateType.message or context.update_type == octobot.UpdateType.inline_query:
                context.reply(message)
            elif context.update_type == octobot.UpdateType.button_press:
                context.reply(context.localize("Error occured"))
                context.edit(message)
