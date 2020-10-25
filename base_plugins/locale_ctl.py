from octobot import CommandHandler, InlineButtonHandler, PluginInfo
import telegram
import octobot.localization
from babel import Locale
import logging
import flag

logger = logging.getLogger("localectl")
inf = PluginInfo("Localization settings")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


@CommandHandler("language", description="Set language", inline_support=False)
def set_locale(bot, ctx):
    if len(ctx.args) == 0:
        kbd = []
        for locales in chunks(list(octobot.localization.AVAILABLE_LOCALES), 4):
            kbd_line = []
            for locale in locales:
                l = Locale.parse(locale)
                try:
                    emoji = flag.flag(l.territory)
                except AttributeError:
                    emoji = flag.flag(locale)
                kbd_line.append(telegram.InlineKeyboardButton(text=emoji + l.display_name, callback_data=f"locale_set:{locale}"))
            kbd.append(kbd_line)
        ctx.reply("Available languages:", reply_markup=telegram.InlineKeyboardMarkup(kbd))
    else:
        try:
            octobot.localization.set_chat_locale(ctx.chat.id, ctx.args[0])
        except ValueError:
            ctx.reply(f"Invalid language {ctx.args[0]}.")
        else:
            ctx.reply(ctx.localize('Language "{locale}" set').format(locale=Locale.parse(ctx.args[0]).display_name))


@InlineButtonHandler("locale_set:")
def set_locale_button(bot, ctx):
    language = ctx.text.split(":")[1]
    try:
        octobot.localization.set_chat_locale(ctx.chat.id, language)
    except ValueError as e:
        logger.error("Failed to set locale: %s", e)
        ctx.edit(f"Invalid language {language}")
        ctx.reply("❌")
    else:
        ctx.edit(ctx.localize('Language "{locale}" set').format(locale=Locale.parse(language).display_name))
        ctx.reply("👌")
