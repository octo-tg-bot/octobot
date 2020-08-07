import jstyleson
import logging

LOGGER = logging.getLogger("Settings")


class _Settings():
    _settings = {}

    def __init__(self):
        self.reload_settings()

    def reload_settings(self):
        settings_backup = self._settings.copy()
        with open("settings.base.json") as f:
            base_settings = jstyleson.load(f)
            self._settings = base_settings
        with open("settings.json", "r") as f:
            settings_user = jstyleson.load(f)
            diff = list(set(settings_user.keys()) - set(base_settings.keys()))
            if len(diff) > 0:
                self._settings = settings_backup
                LOGGER.error("Invalid user settings! Restoring previous settings")
                raise ValueError("User settings has unknown item(s) not defined in base JSON: %s." %
                                 diff)
            self._settings.update(settings_user)
        LOGGER.debug(self._settings)
        LOGGER.info("Settings reloaded")

    def __getattr__(self, item):
        if item in self._settings:
            return self._settings[item]
        else:
            raise KeyError("Unknown settings entry: %s" % item)


Settings = _Settings()
