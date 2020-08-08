import os
from glob import glob
from typing import Union

import redis.exceptions

from settings import Settings

AVAILABLE_LOCALES = list(filter(lambda x: os.path.isdir("locales/" + x), os.listdir("locales")))
print(AVAILABLE_LOCALES)
DEFAULT_LOCALE = "en_US"
try:
    db = redis.Redis(host=Settings.redis_host, port=Settings.redis_port, db=Settings.redis_db, socket_connect_timeout=0.5)
    db.ping()
except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
    REDIS_AVAILABLE = False
else:
    REDIS_AVAILABLE = True


def get_chat_locale(chat_id: Union[int, str]):
    if REDIS_AVAILABLE:
        locale = db.get(f"locale:{chat_id}")
        if locale is None:
            return DEFAULT_LOCALE
        else:
            return locale.decode()
    else:
        return DEFAULT_LOCALE


def set_chat_locale(chat_id: Union[int, str], locale: str):
    if REDIS_AVAILABLE:
        if locale not in AVAILABLE_LOCALES:
            raise ValueError(f"Unknown locale: {locale}. Valid locales are {AVAILABLE_LOCALES}")
        db.set(f"locale:{chat_id}", locale)
    else:
        raise RuntimeError("Locale DB is not up")
