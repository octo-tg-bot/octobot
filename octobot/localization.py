import os
from octobot import Database
from typing import Union

AVAILABLE_LOCALES = ["en_US"] + list(filter(lambda x: os.path.isdir("locales/" + x), os.listdir("locales")))
DEFAULT_LOCALE = "en_US"


def localizable(string: str) -> str:
    """
    Function to mark which strings can be translated. Use for bot command descriptions and such

    :param string: String that can be translated
    :return: That exact same string
    """
    return string


def get_chat_locale(chat_id: Union[int, str]):
    return Database[chat_id].get("locale", DEFAULT_LOCALE)


def set_chat_locale(chat_id: Union[int, str], locale: str):
    if locale not in AVAILABLE_LOCALES:
        raise ValueError(f"Unknown locale: {locale}. Valid locales are {AVAILABLE_LOCALES}")
    Database[chat_id].set("locale", locale)
