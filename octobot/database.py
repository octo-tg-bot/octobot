import redis

from octobot import DatabaseNotAvailable
from settings import Settings


class RedisData:
    def __init__(self, redis_db, chat_id):
        self._redis = redis_db
        self.chat_id = chat_id

    def get(self, item, default=None, dont_decode=False):
        if self._redis is None:
            return default
        else:
            res = self._redis.hget(str(self.chat_id), item)
            if res is None:
                return default
            elif dont_decode:
                return res
            else:
                return res.decode()

    def __getitem__(self, item):
        return self.get(item)

    def set(self, key, value):
        if self._redis is None:
            raise DatabaseNotAvailable
        else:
            return self._redis.hset(str(self.chat_id), key, value)

    def __setitem__(self, key, value):
        return self.set(key, value)


class _Database:
    def __init__(self):
        self.redis = redis.Redis(host=Settings.redis_host, port=Settings.redis_port, db=Settings.redis_db)
        try:
            self.redis.ping()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            self.redis = None

    def __getitem__(self, item):
        item = int(item)
        return RedisData(self.redis, item)


Database = _Database()
