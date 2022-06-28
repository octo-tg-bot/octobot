import logging

from fakeredis.aioredis import FakeRedis
from fastapi import FastAPI, APIRouter

import octobot as ob

from .dependencies import get_bot
from .routers import telegram_webhook

logger = logging.getLogger("Bot")
STATES_EMOJIS = {
    ob.misc.PluginStates.unknown: "❓",
    ob.misc.PluginStates.error: "🐞",
    ob.misc.PluginStates.notfound: "🧐",
    ob.misc.PluginStates.loaded: "👌",
    ob.misc.PluginStates.skipped: "⏩",
    ob.misc.PluginStates.warning: "⚠️",
    ob.misc.PluginStates.disabled: "🔽"
}


def create_startup_msg(bot):
    msg = "obV5 loaded."
    for plugin in bot.plugins.values():
        msg += f"\n{STATES_EMOJIS[plugin['state']]} {plugin['name']}"
        if plugin['state'] != ob.misc.PluginStates.loaded:
            msg += f" - {plugin.state_description}"
    if isinstance(ob.database.redis, FakeRedis):
        msg += "\n⚠️System health warning: Redis not available - using FakeRedis."
    return msg


app = FastAPI(prefix="/api/v1")
main_router = APIRouter(prefix="/api/v1")
main_router.include_router(telegram_webhook.router)

app.include_router(main_router)


@app.on_event("startup")
async def create_bot():
    bot = await get_bot()
    await bot.send_message(ob.settings.owner, create_startup_msg(bot))
