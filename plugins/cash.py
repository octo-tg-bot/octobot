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
from settings import Settings

import octobot

plugin = octobot.PluginInfo(name="Currency Converter")
CURR_TEMPLATE = octobot.localizable("""
%(in)s = %(out)s

<a href="http://free.currencyconverterapi.com/">Powered by Currency convert API</a>
""")
LOGGER = logging.getLogger("/cash")


def number_conv(amount):
    amount = str(amount).lower()
    power = 10 ** (amount.count("k") * 3 + amount.count("m") * 6 + amount.count("b") * 9)
    amount = re.sub("[kmb]", "", amount)
    return float(amount) * power


def get_rate(in_c, out_c):
    rate, status_code = octobot.Database.get_cache(
        "https://free.currconv.com/api/v7/convert?compact=ultra",
        params={
            "q": in_c + "_" + out_c,
            "apiKey": Settings.currency_converter_apikey
        }
    )
    LOGGER.debug(rate)
    if status_code != 200:
        raise requests.HTTPError
    if rate == {}:
        raise NameError("Invalid currency")
    return rate


def convert(in_c, out_c, count):
    rate = get_rate(in_c, out_c)
    out = {}
    out["in"] = "<b>%s</b> <i>%s</i>" % (count, in_c.upper())
    out["out"] = "<b>%s</b> <i>%s</i>" % (round(number_conv(count) * float(list(rate.values())[0]), 2), out_c.upper())
    return out


long_desc = octobot.localizable("""Powered by The Free Currency Converter API
Example usage:

    User:
    /cash 100 RUB USD

    OctoBot:
    100 RUB = 1.66 USD

8/7/2017 10:30pm
Data from Yahoo Finance""")


@octobot.CommandHandler(command=["cash", "currency", "stonks"],
                        description=octobot.localizable("Converts currency"),
                        long_description=long_desc,
                        required_args=3)
def currency(bot, context):
    try:
        try:
            number_conv(context.args[0])
        except ValueError:
            return context.reply(context.localize("{} is not a valid number").format(context.args[0]))
        else:
            rate = convert(context.args[1], context.args[-1], context.args[0])
    except NameError:
        return context.reply(context.localize('Unknown currency specified'))
    except requests.HTTPError:
        return context.reply(context.localize("Currency API is unavailable right now, try later"))
    else:
        return context.reply(context.localize(CURR_TEMPLATE) % rate, parse_mode="HTML", no_preview=True)
