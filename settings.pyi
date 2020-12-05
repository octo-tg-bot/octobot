from typing import Any

LOGGER = ...  # type: Any
FOLDER = ...  # type: Any
Settings = ...  # type: _Settings


class _Settings:
    _settings = ...  # type: Any
    telegram_token = ...  # type: str
    production = ...  # type: bool
    owner = ...  # type: int
    telegram_base_url = ...  # type: str
    telegram_base_file_url = ...  # type: str
    telegram_base_file_url_force = ...  # type: bool
    threads = ...  # type: int
    exclude_plugins = ...  # type: list
    support_url = ...  # type: str
    user_agent = ...  # type: str
    mozamibque_here_token = ...  # type: str
    currency_converter_apikey = ...  # type: str
    imgur_clientid = ...  # type: str
    allowed_chats = ...  # type: list
    disallowed_chat_reason = ...  # type: str
    no_image = ...  # type: str
    sentry = ...  # type: dict_sentry
    redis = ...  # type: dict_redis
    spamwatch = ...  # type: dict_spamwatch
    def __init__(self) -> Any: ...
    def reload_settings(self) -> Any: ...
    def __getattr__(self, item: Any) -> Any: ...
    def get(self, item: Any) -> Any: ...
    def __setitem__(self, key: Any, value: Any) -> Any: ...
    def save_settings_to_disk(self) -> Any: ...

class dotdict(dict):
    __getattr__ = ...  # type: Any
    __setattr__ = ...  # type: Any
    __delattr__ = ...  # type: Any

class dict_sentry(dotdict):
    enabled = ...  # type: bool
    dsn = ...  # type: str
    organization_slug = ...  # type: str
    project_slug = ...  # type: str

class dict_redis(dotdict):
    host = ...  # type: str
    port = ...  # type: int
    db = ...  # type: int

class dict_spamwatch(dotdict):
    api_host = ...  # type: str
    token = ...  # type: str
    default_action = ...  # type: str
