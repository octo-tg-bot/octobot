import octobot
import telegram
import json
inf = octobot.PluginInfo("Stealth mode")


def get_stealthmode_status(context) -> bool:
    return json.loads(context.chat_db.get("stealthmode", 'false'))


def set_stealthmode_status(context, status):
    context.chat_db["stealthmode"] = json.dumps(status)


def delete_commands(bot, context):
    bot.setMyCommands([], scope=telegram.BotCommandScopeChat(context.chat.id))


@octobot.InlineButtonHandler("toggleStealth")
@octobot.permissions(is_admin=True)
def stealthmode_toggle(bot, context):
    if get_stealthmode_status(context):
        bot.deleteMyCommands(
            scope=telegram.BotCommandScopeChat(context.chat.id))
        context.reply(context.localize("Stealth mode is off now."))
        set_stealthmode_status(context, False)
    else:
        delete_commands(bot, context)
        set_stealthmode_status(context, True)
        context.reply(context.localize("Stealth mode is on now."))
    context.edit(**create_stealth_mode_message(context))


STEALTH_MODE_DESCRIPTION = octobot.localizable("Stealthmode helps reduce clutter in chats by hiding bot commands from [/] button,"
                                               " preventing people from accidentally running commands.")

STEALTHMODE_COMMAND_NOTICE = octobot.localizable(
    "\nIf there are still commands in [/] button, click the fix stealth mode button")


def create_stealth_mode_message(context):
    is_stealthmode_on = get_stealthmode_status(context)
    keyboard = [[telegram.InlineKeyboardButton(
        callback_data="toggleStealth", text="Toggle stealth mode")]]
    if is_stealthmode_on:
        keyboard.append(telegram.InlineKeyboardButton(
            callback_data="fixStealth", text=context.localize("Fix stealth mode")))
    return {'text': context.localize(STEALTH_MODE_DESCRIPTION) +
            context.localize("\nStealthmode is <b>{state}</b> right now. "
                             ).format(state=context.localize("enabled")
                                      if is_stealthmode_on else
                                      context.localize("disabled")) +
            (context.localize(
                STEALTHMODE_COMMAND_NOTICE) if is_stealthmode_on else ''),
            'reply_markup': telegram.InlineKeyboardMarkup(keyboard), 'parse_mode': 'html'}


@octobot.CommandHandler(command="stealthmode", description=octobot.localizable("Stealth mode settings"), inline_support=False)
@octobot.supergroup_only
def stealthmode_desc(bot, context):
    mess_kwargs = create_stealth_mode_message(context)
    context.reply(
        **mess_kwargs)
