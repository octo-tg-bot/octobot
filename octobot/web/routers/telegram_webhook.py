import logging
import os

import psutil
import telegram
from fastapi import APIRouter, Body, Depends, HTTPException, Header
from pyngrok import ngrok

import octobot as ob
import octobot.web.dependencies as obweb

router = APIRouter(
    prefix="/telegram",
    dependencies=[Depends(obweb.get_bot)]
)

WEBHOOK_TYPES = {
    "inline_query": ob.InlineQueryContext,
    "callback_query": ob.CallbackContext,
    "message": ob.MessageContext,
    "edited_message": ob.EditedMessageContext,
    "chosen_inline_result": ob.ChosenInlineResultContext
}
logger = logging.getLogger("octobot.web.webhook")


@router.post("/webhook")
async def webhook(bot: ob.OctoBot = Depends(obweb.get_bot), update_dict=Body(), x_telegram_bot_api_secret_token=Header()):
    if x_telegram_bot_api_secret_token != ob.settings.webhook.secret:
        raise HTTPException(403, "Invalid secret token.")
    update = telegram.Update.de_json(update_dict, bot)
    bot.insert_callback_data(update)
    context_type = list(update_dict.keys())[-1]
    if context_type not in WEBHOOK_TYPES:
        raise HTTPException(400, f"Unknown update type: {context_type}")
    message = None
    if update.message:
        message = update.message
    context = WEBHOOK_TYPES[context_type](update, bot, message)
    logger.debug("Incoming update: %s, %s", context, type(context))
    await bot.handle_update(context)
    return "ok"


@router.on_event("startup")
async def setup_webhook():
    tasklist = list((p.name() for p in psutil.process_iter()))
    if not ("ngrok" in tasklist or "ngrok.exe" in tasklist):
        if ob.settings.webhook.ngrok:
            logger.info("Setting up ngrok webhook")
            http_tunnel = ngrok.connect(
                ob.settings.webhook.internal_port, bind_tls=True)
            ob.settings.webhook.external_address = http_tunnel.public_url
            ob.settings.webhook.external_port = 443
            logger.info("Ngrok started at %s",
                        ob.settings.webhook.external_address)
        bot = await obweb.get_bot()
        await bot.delete_webhook()
        webhook_url = ob.settings.webhook.external_address + \
            "/api/v1/telegram/webhook"
        logger.info("Setting up %s", webhook_url)
        await bot.set_webhook(webhook_url,
                              allowed_updates=list(WEBHOOK_TYPES.keys()), secret_token=ob.settings.webhook.secret)
    else:
        logger.error("Ngrok is already set up...")
