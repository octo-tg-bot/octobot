import json
import logging

import redis
import requests

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


def request_create_id(request_type, request_args, request_kwargs):
    return f"request_cache:{request_type}:{json.dumps(request_args)}:{json.dumps(request_kwargs)}"


class _Database:
    """
    Base database class.

    Usage:
    Database[chat_id] to get :class:`RedisData` for chat_id
    """

    def __init__(self):
        self.request_session = requests.Session()
        self.request_session.headers.update({"User-Agent": Settings.user_agent})
        self.redis = redis.Redis(host=Settings.redis["host"], port=Settings.redis["port"], db=Settings.redis["db"])
        try:
            self.redis.ping()
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            logger.error("Error: Redis is not available. That might break the bot in some places.")
            self.redis = None
        else:
            logger.info("Redis connection successful")

        def create_cached_request_function(rtype):
            def cache(*args, **request_kwargs):
                convert_json = request_kwargs.pop("convert_json", True)
                return self.cache_requests(request_type=rtype, convert_json=convert_json, request_args=args,
                                           request_kwargs=request_kwargs)

            return cache

        self.get_cache = create_cached_request_function("GET")
        self.post_cache = create_cached_request_function("POST")

    def __getitem__(self, item):
        item = int(item)
        return RedisData(self.redis, item)

    def _do_request(self, request_type, args, kwargs):
        req = requests.Request(request_type, *args, **kwargs)
        prepped = self.request_session.prepare_request(req)
        resp = self.request_session.send(prepped)
        return resp.content, resp.status_code

    def cache_requests(self, request_type, convert_json, request_args, request_kwargs):
        logger.debug(request_type)
        if self.redis is None:
            logger.warning("DB not available, requests are not cached, beware")
            return self._do_request(request_type, request_args, request_kwargs)
        else:
            db_entry = request_create_id(request_type, request_args, request_kwargs)
            if self.redis.exists(db_entry) == 1:
                logger.debug("Using cached result")
                req = self.redis.get(db_entry)
                if convert_json:
                    req = json.loads(req.decode())
                return req, 200
            else:
                req, status_code = self._do_request(request_type, request_args, request_kwargs)
                if status_code == requests.codes.ok:
                    logger.debug("Status code is 200, saving to redis")
                    self.redis.set(db_entry, req)
                    self.redis.expire(db_entry, 60)
                if convert_json:
                    logger.debug(req)
                    return json.loads(req.decode()), status_code
                return req, status_code


Database = _Database()
