from octobot import CommandHandler, InlineButtonHandler
import telegram
import octobot.localization
from babel import Locale
import logging
logger = logging.getLogger("localectl")

@CommandHandler("language", description="Set language", inline_support=False)
def set_locale(bot, ctx):
    if len(ctx.args) == 0:
        kbd = []
        for locale in octobot.localization.AVAILABLE_LOCALES:
            l = Locale.parse(locale)
            kbd.append(telegram.InlineKeyboardButton(text=l.display_name, callback_data=f"locale_set:{locale}"))
        ctx.reply("Available languages:", reply_markup=telegram.InlineKeyboardMarkup([kbd]))
    else:
        try:
            octobot.localization.set_chat_locale(ctx.chat.id, ctx.args[1])
        except RuntimeError:
            ctx.reply("Can't set language - language database is down. Please contact bot administrator.")
        except ValueError:
            ctx.reply(f"Invalid language {ctx.args[1]}.")

@InlineButtonHandler("locale_set:")
def set_locale_button(bot, ctx):
    language = ctx.text.split(":")[1]
    try:
        octobot.localization.set_chat_locale(ctx.chat.id, language)
    except RuntimeError:
        ctx.edit("Can't set language - language database is down. Please contact bot administrator.")
        ctx.reply("❌")
    except ValueError as e:
        logger.error("Failed to set locale: %s", e)
        ctx.edit(f"Invalid language {language}")
        ctx.reply("❌")
    else:
        ctx.edit(ctx.localize('Language "{locale}" set').format(locale=Locale.parse(language).display_name))
        ctx.reply("👌")