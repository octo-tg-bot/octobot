from typing import Any

LOGGER = ...  # type: Any
FOLDER = ...  # type: Any
Settings = ...  # type: _Settings


class _Settings:
    _settings = ...  # type: Any
    telegram_token = ...  # type: str
    production = ...  # type: bool
    owner = ...  # type: int
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
    exceptions = ...  # type: dict
    redis = ...  # type: dict
    def __init__(self) -> Any: ...
    def reload_settings(self) -> Any: ...
    def __getattr__(self, item: Any) -> Any: ...
    def get(self, item: Any) -> Any: ...
    def __setitem__(self, key: Any, value: Any) -> Any: ...
    def save_settings_to_disk(self) -> Any: ...
