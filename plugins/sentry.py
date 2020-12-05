import html
import os
import sys

import sentry_sdk

import octobot
import octobot.exceptions
from settings import Settings

if not Settings.sentry.enabled:
    raise octobot.DontLoadPlugin("Sentry is disabled")

sentry_sdk.init(
    Settings.sentry.dsn,
    debug=not Settings.production,
    environment=("prod" if Settings.production else "debug"),
    default_integrations=False
)


class SentryHandler(octobot.ExceptionHandler):
    def handle_exception(self, bot, context: octobot.Context, exception):
        with sentry_sdk.configure_scope() as scope:
            scope.set_user(context.user.to_dict())
            scope.set_context("update", context.update.to_dict())
            if isinstance(context._handler, octobot.CommandHandler):
                scope.transaction = f"Command {context._handler.prefix}{context._handler.command[0]} " \
                                    f"({context.update_type})"
            elif isinstance(context._handler, octobot.InlineButtonHandler):
                scope.transaction = f"Inline button {context._handler.prefix}"
            else:
                scope.transaction = "Unknown transaction"
            event_code = sentry_sdk.capture_exception(exception)
        if event_code is None:
            return
        message = context.localize("Event code is <code>{}</code>").format(event_code)
        return message


traceback_handler = SentryHandler()
