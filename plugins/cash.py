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

from settings import Settings

import octobot

plugin = octobot.PluginInfo(name="Currency Converter")
CURR_TEMPLATE = octobot.localizable("""
%(in)s = %(out)s

<a href="http://free.currencyconverterapi.com/">Powered by Currency convert API</a>
""")
LOGGER = plugin.logger


def get_currency_data():
    r = octobot.Database.get_cache("https://free.currconv.com/api/v7/currencies", params={
        "apiKey": Settings.currency_converter_apikey
    })
    if not r.ok:
        LOGGER.warning("Failed to get currency list, conversion using symbols won't work")
        return {}, {}
    data, aliases = r.json()["results"], dict()
    for currency_name, currency_inf in data.items():
        if currency_inf.get("currencySymbol", False):
            aliases[currency_inf["currencySymbol"]] = currency_name
    aliases["$"] = "USD"
    return data, aliases


CURRENCY_DATA, CURRENCY_ALIASES = get_currency_data()


def number_conv(amount):
    amount = str(amount).lower()
    power = 10 ** (amount.count("k") * 3 + amount.count("m") * 6 + amount.count("b") * 9)
    amount = re.sub("[kmb]", "", amount)
    return float(amount) * power


def get_rate(in_c, out_c):
    rate_r = octobot.Database.get_cache(
        "https://free.currconv.com/api/v7/convert?compact=ultra",
        params={
            "q": in_c + "_" + out_c,
            "apiKey": Settings.currency_converter_apikey
        }
    )
    rate_r.raise_for_status()
    rate = rate_r.json()
    LOGGER.debug(rate)

    if rate == {}:
        raise NameError("Invalid currency")
    return rate


def convert(in_c, out_c, count, ctx):
    rate = get_rate(in_c, out_c)
    out = {}
    result = round(number_conv(count) * float(list(rate.values())[0]), 2)
    out['in'] = "<b>{}</b> <i>{}</i>".format(
        format_decimal(number_conv(count), locale=ctx.locale),
        get_currency_name(in_c.upper(), locale=ctx.locale, count=number_conv(count)))
    out['out'] = "<b>{}</b> <i>{}</i>".format(
        format_decimal(result, locale=ctx.locale),
        get_currency_name(out_c.upper(), locale=ctx.locale, count=number_conv(count)))
    return out


long_desc = octobot.localizable("""Powered by The Free Currency Converter API
Example usage:

    User:
    /cash 100 RUB USD

    OctoBot:
    100 RUB = 1.66 USD""")


def get_currency_id(currency: str):
    return CURRENCY_ALIASES.get(currency, currency)


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
            rate = convert(get_currency_id(context.args[1]), get_currency_id(context.args[-1]), context.args[0],
                           context)
    except NameError:
        return context.reply(context.localize('Unknown currency specified'))
    except requests.HTTPError:
        return context.reply(context.localize("Currency API is unavailable right now, try later"))
    else:
        return context.reply(context.localize(CURR_TEMPLATE) % rate, parse_mode="HTML", no_preview=True)
