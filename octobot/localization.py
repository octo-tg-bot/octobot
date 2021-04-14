import os

import telegram

from octobot import Database
from typing import Union
import babel
AVAILABLE_LOCALES = ["en-us"]
if os.path.exists("locales"):
    AVAILABLE_LOCALES += list(filter(lambda x: os.path.isdir("locales/" + x), os.listdir("locales")))
    try:
        AVAILABLE_LOCALES.remove("__pycache__")
    except ValueError:
        pass
# for locale in babel.core.LOCALE_ALIASES.values():
#     if locale not in AVAILABLE_LOCALES:
#         AVAILABLE_LOCALES.append(locale)
DEFAULT_LOCALE = "en-us"


def localizable(string: str) -> str:
    """
    Function to mark which strings can be translated. Use for bot command descriptions and such

    :param string: String that can be translated
    :return: That exact same string
    """
    return string


def get_user_locale(user: telegram.User):
    user_id = user.id
    locale = Database[user_id].get("locale", False)
    if not locale:
        locale = user.language_code
        if locale not in AVAILABLE_LOCALES and locale is not None:
            locale = locale.split("-")[0]
            if locale not in AVAILABLE_LOCALES:
                locale = DEFAULT_LOCALE
        elif locale is None:
            locale = DEFAULT_LOCALE
    return locale


def get_chat_locale(update: telegram.Update):
    if update.effective_chat is None:
        locale = get_user_locale(update.effective_user)
    else:
        chat_id = update.effective_chat.id
        locale = Database[chat_id].get("locale", False)
        if not locale:
            locale = get_user_locale(update.effective_user)
    return locale


def set_chat_locale(chat_id: Union[int, str], locale: str):
    if locale not in AVAILABLE_LOCALES:
        raise ValueError(f"Unknown locale: {locale}. Valid locales are {AVAILABLE_LOCALES}")
    Database[chat_id].set("locale", locale)
