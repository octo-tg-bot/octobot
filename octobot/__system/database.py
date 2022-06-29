import json
import logging
import os
from aiohttp import ClientSession
from aiohttp_client_cache import CachedSession, RedisBackend

import fakeredis.aioredis
import redis.asyncio as redispy
from redis import exceptions as rediserr
from .settings import settings

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


req_kw = {"headers": {'User-Agent': settings.user_agent}}


class Database:
    """
    Base database class.

    Usage:
    `async with database[chat_id] as chat_db:` to get :class:`RedisData` for chat_id
    """
    booted = False

    def __init__(self):
        self.requests = ClientSession(**req_kw)
        self.redis = fakeredis.aioredis.FakeRedis()

    async def finish_boot(self):
        assert not self.booted
        if not os.environ.get("ob_testing", False):
            redis = redispy.from_url(
                settings.redis_url, decode_responses=True)
            try:
                await redis.ping()
            except (rediserr.ConnectionError, rediserr.TimeoutError):
                logger.error(
                    "Error: Redis is not available. That might break the bot in some places.")
            else:
                self.redis = redis
                self.requests = CachedSession(
                    cache=RedisBackend(address=settings.redis_url), **req_kw)
                logger.info("Redis connection successful")
        else:
            logger.info("Testing environment - using fakeredis")

    @property
    def r(self):
        return self.requests

    def __getitem__(self, item):
        item = int(item)
        return RedisData(self.redis, item)


class DatabaseNotAvailable(ConnectionError):
    """Gets raised if database cant be accessed"""
    pass
