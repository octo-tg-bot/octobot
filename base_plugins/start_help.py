import base64
import html

import octobot
from octobot import catalogs
import telegram
from settings import Settings
import logging

logger = logging.getLogger("StartHelp")

info = octobot.PluginInfo(octobot.localizable("Usual bot commands"))

@octobot.CommandHandler("start", description="Bot generic description and stuff", inline_support=False)
def start(bot: octobot.OctoBot, ctx: octobot.Context):
    if ctx.query == "":
        kbd = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton(ctx.localize("Command list"),
                                           url=f"https://t.me/{bot.me.username}?start=help")],
            [telegram.InlineKeyboardButton(ctx.localize("Support chat"), url=Settings.support_url)]
        ])
        ctx.reply(ctx.localize(
            "Hi! I am {bot.me.first_name}, a Telegram bot with features and bugs and blah blah, noone reads /start anyway.").format(
            bot=bot), reply_markup=kbd)
    else:
        # Proxify to other command
        update = ctx.update
        if ctx.args[0].startswith("b64-"):
            b64data = ctx.args[0].replace("b64-", "", 1)
            data = base64.urlsafe_b64decode(b64data)
            logger.debug(f'proxying b64 command {data} ({b64data})')
            update.message.text = data.decode()
        else:
            update.message.text = "/" + ctx.args[0]
            logger.debug("proxying plaintext command %s", update.message.text)
        bot.handle_update(bot, update)


@catalogs.CatalogHandler("help", description="Command list and stuff", inline_support=False, query_required=False)
def help_command(query, idx, max_amount, bot: octobot.OctoBot, ctx: octobot.Context):
    del query, max_amount
    if ctx.chat.type == "supergroup":
        max_amount = 5
    else:
        max_amount = 15
    idx = int(idx)
    handlers = []
    if idx < 0:
        raise catalogs.CatalogCantGoBackwards
    for handlers_prioritylist in list(bot.handlers.values()):
        for handler in handlers_prioritylist:
            if isinstance(handler, octobot.CommandHandler) and not handler.hidden:
                handlers.append(handler)
    handlers = [handlers[x:x + max_amount] for x in range(0, len(handlers), max_amount)]
    handlers_msg = ""
    if len(handlers) - 1 < idx:
        raise catalogs.CatalogCantGoDeeper
    last_plugin = ""
    for handler in handlers[idx]:
        if last_plugin != handler.plugin.name:
            last_plugin = handler.plugin.name
            handlers_msg += f"<b>{ctx.localize(handler.plugin.name)}:</b>\n"
        handlers_msg += '{commands} – {description}. <i><a href="t.me/{bot.me.username}?start=b64-{command}">{learnmore}</a></i>\n'.format(
            commands=", ".join(handler.commandlist),
            description=html.escape(ctx.localize(handler.description)),
            bot=bot,
            command=base64.urlsafe_b64encode(("/helpextra " + handler.command[0]).encode()).decode(),
            learnmore=ctx.localize("More…")
        )
    catalog = catalogs.Catalog(results=[catalogs.CatalogKeyArticle(handlers_msg, parse_mode="HTML")],
                               current_index=idx + 1, next_offset=idx + 1, previous_offset=idx - 1,
                               max_count=len(handlers))
    return catalog


@octobot.CommandHandler("helpextra", hidden=True)
def help_extra(bot, ctx: octobot.Context):
    if ctx.query != "":
        cmd = ctx.query
        for handlers in bot.handlers.values():
            for handler in handlers:
                if isinstance(handler, octobot.CommandHandler) and cmd in handler.command:
                    message = "{helpfor} {command}.\n{description}\n\n{long_description}".format(
                        helpfor=ctx.localize("Help for"),
                        command=handler.prefix + ctx.query,
                        description=html.escape(handler.description),
                        long_description=html.escape(handler.long_description)
                    )
                    ctx.reply(message)
                    return
