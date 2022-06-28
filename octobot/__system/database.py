import json
import logging
import os

import fakeredis.aioredis
import redis

logger = logging.getLogger("Redis")


class RedisData:
    """
    Redis chat/user data class. Can be accessed like dictionary.
    """

    def __init__(self, redis_db, chat_id):
        self._redis = redis_db
        self.chat_id = chat_id

    @property
    def hashmap_name(self):
        return f"settings:{self.chat_id}"

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
            res = self._redis.hget(self.hashmap_name, key)
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
            return self._redis.hset(self.hashmap_name, key, value)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __contains__(self, key):
        return self._redis.hexists(self.hashmap_name, key)


def request_create_id(request_type, request_args, request_kwargs):
    return f"request_cache:{request_type}:{json.dumps(request_args)}:{json.dumps(request_kwargs)}"


def http_cache(rtype):
    def decorator(_):
        def cache(*args, **request_kwargs):
            self = args[0]
            return self.cache_requests(request_type=rtype, request_args=args[1:],
                                       request_kwargs=request_kwargs)

        return cache

    return decorator


class Database:
    """
    Base database class.

    Usage:
    database[chat_id] to get :class:`RedisData` for chat_id
    """
    redis: redis.Redis

    def __init__(self, Settings):
        if not os.environ.get("ob_testing", False):
            self.redis = redis.Redis(
                host=Settings.redis["host"], port=Settings.redis["port"], db=Settings.redis["db"])
            try:
                self.redis.ping()
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                logger.error(
                    "Error: Redis is not available. That might break the bot in some places.")
                self.redis = fakeredis.aioredis.FakeRedis()
            else:
                logger.info("Redis connection successful")
        else:
            logger.info("Testing environment - using fakeredis")
            self.redis = fakeredis.aioredis.FakeRedis()

    def __getitem__(self, item):
        item = int(item)
        return RedisData(self.redis, item)


class DatabaseNotAvailable(ConnectionError):
    """Gets raised if database cant be accessed"""
    pass
