# The MIT License (MIT)
# Copyright (c) 2019 OctoNezd
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

import logging
import re

import requests
from babel.numbers import format_currency, format_decimal, get_currency_name
from octobot.dataclass import Suggestion

from settings import Settings

import octobot

plugin = octobot.PluginInfo(name="Currency Converter")
CURR_TEMPLATE = octobot.localizable("""
%(in)s = %(out)s

<a href="http://exchangerate.host/">Powered by exchangerate.host</a>
""")
LOGGER = plugin.logger


def number_conv(amount):
    amount = str(amount).lower()
    power = 10 ** (amount.count("k") * 3 + amount.count("m")
                   * 6 + amount.count("b") * 9)
    amount = re.sub("[kmb]", "", amount)
    return float(amount) * power


def get_rate(in_c, out_c):
    rate_r = octobot.Database.get_cache(
        "https://api.exchangerate.host/convert",
        params={
            "from": in_c,
            "to": out_c
        }
    )
    rate_r.raise_for_status()
    rate = rate_r.json()["result"]
    LOGGER.debug(rate)
    if rate is None:
        raise NameError("Invalid currency")
    return rate


def convert(in_c, out_c, count, ctx):
    rate = get_rate(in_c, out_c)
    out = {}
    result = round(number_conv(count) * rate, 2)
    out['in'] = "<b>{}</b> <i>{}</i>".format(
        format_decimal(number_conv(count), locale=ctx.locale),
        get_currency_name(in_c.upper(), locale=ctx.locale, count=number_conv(count)))
    out['out'] = "<b>{}</b> <i>{}</i>".format(
        format_decimal(result, locale=ctx.locale),
        get_currency_name(out_c.upper(), locale=ctx.locale, count=number_conv(count)))
    return out


long_desc = octobot.localizable("""Powered by exchangerate.host
Example usage:

    User:
    /cash 100 RUB USD

    OctoBot:
    100 RUB = 1.66 USD""")


@octobot.CommandHandler(command=["cash", "currency", "stonks"],
                        description=octobot.localizable("Converts currency"),
                        long_description=long_desc,
                        required_args=3,
                        suggestion=Suggestion("https://i.kym-cdn.com/photos/images/newsfeed/001/499/826/2f0.png", octobot.localizable("Currency conversion"), "cash 200 rub usd"))
def currency(bot, context):
    try:
        try:
            number_conv(context.args[0])
        except ValueError:
            return context.reply(context.localize("{} is not a valid number").format(context.args[0]))
        else:
            rate = convert(context.args[1], context.args[-1], context.args[0],
                           context)
    except NameError:
        return context.reply(context.localize('Unknown currency specified'))
    except requests.HTTPError:
        return context.reply(context.localize("Currency API is unavailable right now, try later"))
    else:
        return context.reply(context.localize(CURR_TEMPLATE) % rate, parse_mode="HTML", no_preview=True)
