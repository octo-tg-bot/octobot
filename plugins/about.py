# The MIT License (MIT)
# Copyright (c) 2020 OctoNezd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.
import octobot
import telegram

plugin = octobot.PluginInfo("About bot")


@octobot.CommandHandler(command="about",
                        description=octobot.localizable("About bot"),
                        hidden=False)
def about(bot, context):
    about_string = context.localize("OctoBot version <code>{ob_version}</code>\n" + \
                                    "Python-Telegram-Bot version: <code>{ptb_version}</code>\n" + \
                                    '<a href="https://github.com/octo-tg-bot/">GitHub page</a>\n').format(
        ob_version=octobot.__version__,
        ptb_version=telegram.__version__
    ) + (context.localize("🐳Running inside Docker") if octobot.is_docker else context.localize("🖥️Running on normal system"))
    context.reply(text=about_string, parse_mode="HTML", no_preview=True)
