import os
import sys
if not os.path.exists("octobot"):
    os.chdir("..")
try:
    import octobot
except ModuleNotFoundError:
    sys.path.append(os.getcwd())
    import octobot
import logging

logging.basicConfig(level=0)

os.environ["DRY_RUN"] = "1"
bot = octobot.OctoBot([])