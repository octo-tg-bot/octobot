import json
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
            base_settings = toml.load(f, dotdict)
            self.update_settings(base_settings)
        try:
            with open(FOLDER + "/settings.toml", "r") as f:
                settings_user = toml.load(f, dotdict)
                diff = list(set(settings_user.keys()) - set(base_settings.keys()))
                if len(diff) > 0:
                    self.update_settings(settings_backup)
                    LOGGER.error("Invalid user settings! Restoring previous settings")
                    raise ValueError("User settings has unknown item(s) not defined in base TOML: %s." %
                                     diff)
                self._settings.update(settings_user)
        except FileNotFoundError:
            LOGGER.critical(
                "Failed to find settings.toml!")
        LOGGER.debug("Iterating over os.environ")
        for key in os.environ:
            key = key.lower()
            LOGGER.debug(key)
            if key.startswith("ob_"):
                try:
                    self._settings[key[3:]] = json.loads(os.environ[key])
                except json.JSONDecodeError as e:
                    LOGGER.warning("The key %s has an invalid JSON value of '%s' (error: %s), loading just as plain string", key, os.environ[key], e)
                    self._settings[key[3:]] = os.environ[key]
                else:
                    LOGGER.debug("Loaded settings key %s from environment", key)
        LOGGER.debug(self._settings)
        LOGGER.info("Settings reloaded")

    def update_settings(settings: dict):
        self._settings = settings

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


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


Settings: _Settings = _Settings()
