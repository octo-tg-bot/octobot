import os

import toml
import logging

LOGGER = logging.getLogger("Settings")

FOLDER = os.path.abspath(os.path.dirname(__file__))


class _Settings():
    _settings: dict = {}

    def __init__(self):
        self.reload_settings()

    def reload_settings(self) -> None:
        settings_backup = self._settings.copy()
        with open(FOLDER + "/settings.base.toml") as f:
            base_settings = toml.load(f)
            self._settings = base_settings
        try:
            with open(FOLDER + "/settings.toml", "r") as f:
                settings_user = toml.load(f)
                diff = list(set(settings_user.keys()) - set(base_settings.keys()))
                if len(diff) > 0:
                    self._settings = settings_backup
                    LOGGER.error("Invalid user settings! Restoring previous settings")
                    raise ValueError("User settings has unknown item(s) not defined in base TOML: %s." %
                                     diff)
                self._settings.update(settings_user)
        except FileNotFoundError:
            LOGGER.critical(
                "Failed to find settings.toml! Continuing anyway cause who knows, maybe doc is getting built?")
        LOGGER.debug(self._settings)
        LOGGER.info("Settings reloaded")

    def __getattr__(self, item:str):
        if item in self._settings:
            return self._settings[item]
        else:
            raise KeyError("Unknown settings entry: %s" % item)

    def get(self, item: str):
        if item in self._settings:
            return self._settings[item]

    def __setitem__(self, key: str, value):
        return self._settings.__setitem__(key, value)

    def save_settings_to_disk(self) -> None:
        try:
            with open(FOLDER + "/settings.toml", "w") as f:
                toml.dump(self._settings, f)
        except FileNotFoundError:
            LOGGER.critical(
                "Failed to find settings.toml! Continuing anyway cause who knows, maybe doc is getting built?")


Settings: _Settings = _Settings()
