import os

import telegram

from octobot import Database
from typing import Union

AVAILABLE_LOCALES = ["en"] + list(filter(lambda x: os.path.isdir("locales/" + x), os.listdir("locales")))
DEFAULT_LOCALE = "en"


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
        if locale not in AVAILABLE_LOCALES:
            locale = locale.split("-")[0]
            if locale not in AVAILABLE_LOCALES:
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
