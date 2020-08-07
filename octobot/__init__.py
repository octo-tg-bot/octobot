
from octobot.handlers import *
from octobot.loader import OctoBot, PluginStates
from octobot.classes import *
import logging

class UnknownUpdate(ValueError):
    pass

class LoaderCommand(Exception):
    pass

class StopHandling(LoaderCommand):
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    ml = OctoBot([])
    print(ml.discover_plugins())
