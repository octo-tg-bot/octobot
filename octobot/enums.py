from enum import Enum


class PluginStates(Enum):
    loaded = 0
    unknown = 1
    error = 2
    notfound = 3
    skipped = 4
    warning = 5
    disabled = 6