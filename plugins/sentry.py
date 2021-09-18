import html
import os
import sys

import requests
import sentry_sdk
import telegram

import octobot
import octobot.exceptions
from settings import Settings

if not Settings.sentry.enabled:
    raise octobot.DontLoadPlugin("Sentry is disabled")
plugin = octobot.PluginInfo("Sentry", can_disable=False)
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
                                    f"({type(context)})"
            elif isinstance(context._handler, octobot.InlineButtonHandler):
                scope.transaction = f"Inline button {context._handler.prefix}"
            else:
                scope.transaction = "Unknown transaction"
            event_code = sentry_sdk.capture_exception(exception)
        if event_code is None:
            return
        message = context.localize(
            "Event code is <code>{}</code>").format(event_code)
        return message, [telegram.InlineKeyboardButton(
            text=context.localize("Provide feedback"), switch_inline_query_current_chat=f"err_feedback {event_code} ")]


@octobot.InlineQueryHandler("err_feedback")
def feedback_handle_query(bot, ctx):
    if len(ctx.args) > 1 and len(ctx.args[0]) == 32:
        answer = telegram.InlineQueryResultArticle(
            id="feedback",
            title=ctx.localize("Click here to submit your feedback"),
            description=" ".join(ctx.args[1:]),
            input_message_content=telegram.InputTextMessageContent(
                ctx.localize("Thanks you for your feedback! Feel free to delete this message"))
        )
    elif len(ctx.args) > 0 and len(ctx.args[0]) != 32:
        answer = telegram.InlineQueryResultArticle(
            id="fail-feedback",
            title=ctx.localize("Invalid event ID"),
            description=ctx.localize(
                "Did you accidentally deleted the feedback event ID?"),
            input_message_content=telegram.InputTextMessageContent(
                ctx.localize("Feel free to delete this message"))
        )
    else:
        answer = telegram.InlineQueryResultArticle(
            id="fail-feedback",
            title=ctx.localize("You hadn't wrote the feedback."),
            input_message_content=telegram.InputTextMessageContent(
                ctx.localize("Feel free to delete this message"))
        )
    ctx.replied = True
    ctx.update.inline_query.answer(
        [answer], is_personal=True, cache_time=360 if Settings.production else 0)


@octobot.ChosenInlineResultHandler("feedback")
def feedback_handle_inresult(bot, ctx):
    feedback = ' '.join(ctx.query.split()[1:])
    r = requests.post(f"https://sentry.io/api/0/projects/{Settings.sentry.organization_slug}/"
                      f"{Settings.sentry.project_slug}/user-feedback/",
                      headers={
                          "Authorization": "DSN " + Settings.sentry.dsn
                      },
                      json=dict(
                          event_id=ctx.args[0],
                          name=ctx.user.first_name,
                          email=f"{ctx.user.id}_{ctx.user.username}@telegram.domain",
                          comments=feedback
                      ))
    plugin.logger.debug(r.text)


traceback_handler = SentryHandler()
