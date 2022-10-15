from settings import Settings
import octobot
import json
import telegram
import secrets
import html
info = octobot.PluginInfo("Spoilers")
logger = info.logger


class FileTypes:
    FILE_TYPE_PHOTO = "photo"
    FILE_TYPE_AUDIO = "audio"
    FILE_TYPE_VIDEO = "video"
    FILE_TYPE_DOCUMENT = "document"


def create_spoiler_keyboard(spoiler_id, context: octobot.Context, bot: octobot.OctoBot):
    spoiler_url = bot.generate_startlink(f"/spoiler_show {spoiler_id}")
    reply_markup = telegram.InlineKeyboardMarkup.from_column([

        telegram.InlineKeyboardButton(
            context.localize("Show spoiler"),
            url=spoiler_url
        ),
        telegram.InlineKeyboardButton(context.localize(
            "Share spoiler"), switch_inline_query=f"spoiler_send {spoiler_id}")
    ])
    return reply_markup


@octobot.CommandHandler(command="spoiler",
                        description=octobot.localizable("Create spoiler"),
                        inline_support=False
                        )
def make_spoiler(bot: octobot.OctoBot, context: octobot.Context):
    spoiler_id = secrets.token_hex(8)
    spoiler_key = "spoiler:" + spoiler_id
    msg = context.update.message
    attachment = msg.photo or msg.audio or msg.document or msg.video
    file_type = None
    text_content = " ".join((msg.caption or msg.text).split(" ")[1:])
    if len(text_content) == 0 and attachment is None:
        return context.reply(context.localize("You didn't specify text for spoiler or attach image"))
    if isinstance(attachment, list):
        attachment = attachment[0]
    if attachment is not None:
        attachment = attachment.file_id

    if msg.photo:
        file_type = FileTypes.FILE_TYPE_PHOTO
    elif msg.audio:
        file_type = FileTypes.FILE_TYPE_AUDIO
    elif msg.video:
        file_type = FileTypes.FILE_TYPE_VIDEO
    elif msg.document:
        file_type = FileTypes.FILE_TYPE_DOCUMENT
    octobot.Database.redis.hset(spoiler_key, mapping={
        "text": json.dumps(text_content),
        "file_id": json.dumps(attachment),
        "file_type": json.dumps(file_type)
    })
    octobot.Database.redis.expire(spoiler_key, Settings.spoiler_ttl)
    logger.debug("created spoiler: %s", spoiler_id)
    reply_markup = create_spoiler_keyboard(spoiler_id, context, bot)
    if context.chat.type != context.chat.PRIVATE:
        try:
            msg.delete()
        except telegram.error.TelegramError:
            pass
        context.reply(
            context.localize("{user_mention} created a spoiler!").format(
                user_mention=context.user.mention_html()),
            reply_markup=reply_markup,
            parse_mode="HTML")
    else:
        context.reply(context.localize(
            "Spoiler created"), reply_markup=reply_markup)


@octobot.CommandHandler(command="spoiler_show",
                        description="show spoiler",
                        hidden=True, inline_support=False,
                        required_args=1
                        )
def spoiler_show(bot: octobot.OctoBot, context: octobot.Context):
    spoiler_id = context.args[0]
    spoiler_key = "spoiler:" + spoiler_id
    spoiler_b = octobot.Database.redis.hgetall(spoiler_key)
    if not spoiler_b:
        context.reply(context.localize(
            "Invalid spoiler ID specified. NOTE: Spoilers die after a week."))
        return
    spoiler = {}
    for k, v in spoiler_b.items():
        spoiler[k.decode()] = json.loads(v)
    msg = context.update.message
    logger.debug("showing spoiler: %s", spoiler)
    if spoiler["file_id"] is not None:
        args = [spoiler["file_id"]]
        kwargs = dict(caption=spoiler["text"])
        match spoiler["file_type"]:
            case FileTypes.FILE_TYPE_PHOTO:
                msg.reply_photo(*args, **kwargs)
            case FileTypes.FILE_TYPE_AUDIO:
                msg.reply_audio(*args, **kwargs)
            case FileTypes.FILE_TYPE_VIDEO:
                msg.reply_video(*args, **kwargs)
            case FileTypes.FILE_TYPE_DOCUMENT:
                msg.reply_document(*args, **kwargs)
            case _:
                msg.reply_text("Invalid spoiler data. This should not happen.")
    else:
        context.reply(spoiler["text"])


@octobot.CommandHandler(command="spoiler_send",
                        description="send spoiler",
                        hidden=True,
                        required_args=1
                        )
def spoiler_send(bot: octobot.OctoBot, context: octobot.Context):
    spoiler_id = context.args[0]
    if len(context.args) > 1:
        spoiler_desc = " ".join(context.args[1:])
    else:
        spoiler_desc = context.localize(
            "Shared spoiler, no description (you can set it by typing your desc after spoiler id!)")
    reply_markup = create_spoiler_keyboard(spoiler_id, context, bot)
    context.reply(
        "<i>{}</i>".format(html.escape(spoiler_desc)), reply_markup=reply_markup, parse_mode="HTML")
