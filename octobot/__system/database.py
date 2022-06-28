import json
import logging
import os

import fakeredis.aioredis
import aioredis as redis

logger = logging.getLogger("Redis")


class RedisData(dict):
    """
    Redis chat/user data class. Can be accessed like dictionary.
    """
    _pending = {}

    def __init__(self, redis_db, chat_id):
        self._redis = redis_db
        self.chat_id = chat_id
        super(RedisData, self).__init__()

    @property
    def hashmap_name(self):
        return f"settings:{self.chat_id}"

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
        self._pending[key] = value
        self[key] = value

    def __setitem__(self, key, value):
        self._pending[key] = value
        super(RedisData, self).__setitem__(key, value)

    async def refresh(self):
        self.clear()
        self.update(await self._redis.hgetall(self.hashmap_name))
    __aenter__ = refresh

    async def flush(self, *_):
        logger.debug("flushing database changes for %s", self.hashmap_name)
        for key, value in self._pending.items():
            await self._redis.hset(self.hashmap_name, key, value)
        self._pending.clear()
    __aexit__ = flush


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
    `async with database[chat_id] as chat_db:` to get :class:`RedisData` for chat_id
    """
    redis: redis.Redis

    def __init__(self, Settings):
        if not os.environ.get("ob_testing", False):
            self.redis = redis.Redis(
                host=Settings.redis["host"], port=Settings.redis["port"], db=Settings.redis["db"], decode_responses=True)
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
