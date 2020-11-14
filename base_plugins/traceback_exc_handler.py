import html
import os
import sys

import octobot
import octobot.exceptions
from settings import Settings

if Settings.production:
    raise octobot.DontLoadPlugin("Unsafe to use traceback exception handler in production")


class TracebackHandler(octobot.ExceptionHandler):
    def handle_exception(self, bot, context, exception):
        message = [
            context.localize("Error description: <code>{error}</code>").format(error=html.escape(str(exception)))]
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        message.append(
            context.localize("On line {line} in <code>{fname}</code>").format(line=exc_tb.tb_lineno, fname=fname))
        return "\n".join(message)


traceback_handler = TracebackHandler()
