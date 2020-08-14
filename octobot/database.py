import logging

import redis

from octobot import DatabaseNotAvailable
from settings import Settings

logger = logging.getLogger("Redis")


class RedisData:
    """
    Redis chat/user data class. Can be accessed like dictionary.
    """
    def __init__(self, redis_db, chat_id):
        self._redis = redis_db
        self.chat_id = chat_id

    def get(self, key, default=None, dont_decode=False):
        """
        Gets key from database. If database cant be accessed or key cant be found, will return value of `default` param

        :param item: Key to lookup
        :type item: str
        :param default: "Default" value
        :param dont_decode: If value should be decoded from bytes or not. Defaults to False
        :type dont_decode: bool
        :return: The lookup results.
        """
        if self._redis is None:
            return default
        else:
            res = self._redis.hget(str(self.chat_id), key)
            if res is None:
                return default
            elif dont_decode:
                return res
            else:
                return res.decode()

    def __getitem__(self, item):
        return self.get(item)

    def set(self, key, value):
        """
        Sets key to value

        :param key: Key to set
        :type key: str
        :param value: Value
        :type value: any
        :raises: :exc:`octobot.exceptions.DatabaseNotAvailable` if database is not accessible
        :return:
        """
        if self._redis is None:
            raise DatabaseNotAvailable
        else:
            return self._redis.hset(str(self.chat_id), key, value)

    def __setitem__(self, key, value):
        return self.set(key, value)


class _Database:
    """
    Base database class.

    Usage:
    Database[chat_id] to get :class:`RedisData` for chat_id
    """
    def __init__(self):
        self.redis = redis.Redis(host=Settings.redis["host"], port=Settings.redis["port"], db=Settings.redis["db"])
        try:
            self.redis.ping()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            logger.error("Error: Redis is not available. That might break the bot in some places.")
            self.redis = None
        else:
            logger.info("Redis connection successful")

    def __getitem__(self, item):
        item = int(item)
        return RedisData(self.redis, item)


Database = _Database()
