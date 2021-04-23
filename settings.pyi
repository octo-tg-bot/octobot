from typing import Any

LOGGER: Any
FOLDER: Any
Settings: _Settings


class _Settings:
    _settings: Any
    telegram_token: str
    production: bool
    owner: int
    telegram_base_url: str
    telegram_base_file_url: str
    telegram_base_file_url_force: bool
    threads: int
    exclude_plugins: list
    support_url: str
    user_agent: str
    mozamibque_here_token: str
    currency_converter_apikey: str
    imgur_clientid: str
    allowed_chats: list
    disallowed_chat_reason: str
    no_image: str
    sentry: dict_sentry
    redis: dict_redis
    spamwatch: dict_spamwatch
    def __init__(self) -> Any: ...
    def reload_settings(self) -> Any: ...
    def update_settings(settings: Any) -> Any: ...
    def __getattr__(self, item: Any) -> Any: ...
    def get(self, item: Any) -> Any: ...
    def __setitem__(self, key: Any, value: Any) -> Any: ...
    def save_settings_to_disk(self) -> Any: ...

class dotdict(dict):
    __getattr__: Any
    __setattr__: Any
    __delattr__: Any

class dict_sentry(dotdict):
    enabled: bool
    dsn: str
    organization_slug: str
    project_slug: str

class dict_redis(dotdict):
    host: str
    port: int
    db: int

class dict_spamwatch(dotdict):
    api_host: str
    token: str
    default_action: str
