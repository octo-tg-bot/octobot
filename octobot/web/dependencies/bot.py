import logging
import sys
from functools import lru_cache

from aiohttp import ClientSession

import octobot as ob

logger = logging.getLogger("bot")
bot = None


async def get_bot() -> ob.OctoBot:
    global bot
    if bot is None:
        if ob.settings.telegram_base_url != "https://api.telegram.org/bot":
            with ClientSession() as session:
                r = session.get(
                    f"https://api.telegram.org/bot{ob.settings.telegram_token}/logOut")
            logger.info("Using local bot API, logout result: %s", r.text)
        bot = await ob.OctoBot.create(sys.argv[1:], ob.settings)
        if ob.settings.telegram_base_file_url_force:
            logger.warning("Forcefully overriding base url")
            bot.base_file_url = ob.settings.telegram_base_file_url
        logger.debug("API endpoint: %s", bot.base_url)
        logger.debug("API file endpoint: %s", bot.base_file_url)
    return bot
