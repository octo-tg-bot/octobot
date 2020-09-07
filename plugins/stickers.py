# The MIT License (MIT)
# Copyright (c) 2020 OctoNezd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

import logging
from io import BytesIO

from PIL import Image
from telegram.error import BadRequest, TimedOut
import octobot

LOGGER = logging.getLogger("Sticker Optimizer")
PLUGINVERSION = 2
maxwidth, maxheight = 512, 512
# Always name this variable as `plugin`
# If you dont, module loader will fail to load the plugin!
inf = octobot.PluginInfo(name=octobot.localizable("Stickers"),
                         reply_kwargs={"editable": False}
                         )


class NoImageProvided(ValueError): pass


def resize_sticker(image: Image):
    resz_rt = min(maxwidth / image.width, maxheight / image.height)
    sticker_size = [int(image.width * resz_rt), int(image.height * resz_rt)]
    if sticker_size[0] > sticker_size[1]:
        sticker_size[0] = 512
    else:
        sticker_size[1] = 512
    image = image.resize(sticker_size, Image.ANTIALIAS)
    io_out = BytesIO()
    quality = 100
    image.convert("RGBA").save(io_out, "PNG", quality=quality)
    io_out = BytesIO()
    image.save(io_out, "PNG", optimize=True)
    io_out.seek(0)
    return io_out


def create_pack_name(bot, update, personal=False):
    if personal:
        uid = update.message.from_user.id
    else:
        uid = str(update.message.chat_id)[1:]
    name = f"group_{str(uid)}_by_{bot.getMe().username}"
    return name


def get_chat_creator(chat):
    for admin in chat.get_administrators():
        if admin.status == 'creator':
            return admin.user.id


def get_file_id_from_message(message):
    if message.photo:
        LOGGER.debug(message.photo)
        fl = message.photo[-1]
    elif message.document:
        fl = message.document
    elif message.sticker:
        fl = message.sticker
    elif message.reply_to_message:
        fl = get_file_id_from_message(message.reply_to_message)
    else:
        raise NoImageProvided()
    return fl


def get_file_from_message(bot, update):
    io = BytesIO()
    file_id = get_file_id_from_message(update.message).file_id
    fl = bot.getFile(file_id)
    fl.download(out=io)
    io.seek(0)
    return Image.open(io)


@octobot.CommandHandler(command="sticker_optimize",
                        description="Optimizes image/file for telegram sticker",
                        inline_support=False)
def sticker_optimize(bot, ctx):
    try:
        image = get_file_from_message(bot, ctx.update)
    except NoImageProvided:
        return ctx.reply(ctx.localize("No image as photo/file provided."), failed=True)
    except Image.DecompressionBombError:
        return ctx.reply(ctx.localize("Attempting to make image bombs, are we?"), failed=True)
    except OSError:
        return ctx.reply(ctx.localize("This file doesn't look like image file"), failed=True)
    sticker = resize_sticker(image)
    doc = ctx.update.message.reply_document(caption=ctx.localize("Preview:"), document=sticker)
    sticker.seek(0)
    doc.reply_sticker(sticker)


@octobot.CommandHandler("group_pack_add", octobot.localizable("Adds sticker to group stickerpack"), inline_support=False)
@octobot.supergroup_only
@octobot.permissions(is_admin=True)
def gsticker_add(bot, ctx):
    args = ctx.args
    if len(args) > 0:
        emoji = args[0]
    else:
        emoji = "🤖"
    try:
        try:
            image = resize_sticker(get_file_from_message(bot, ctx.update))
        except NoImageProvided:
            return ctx.reply(ctx.localize("No image as photo/file provided."), failed=True)
        except OverflowError:
            return ctx.reply(ctx.localize("Failed to compress image after 8 tries"), failed=True)
        except Image.DecompressionBombError:
            return ctx.reply(ctx.localize("Attempting to make image bombs, are we?"), failed=True)
        except OSError:
            return ctx.reply(ctx.localize("This file doesn't look like image file"), failed=True)
        try:
            bot.addStickerToSet(user_id=get_chat_creator(ctx.update.message.chat),
                                name=create_pack_name(bot, ctx.update),
                                png_sticker=image, emojis=emoji)
        except BadRequest:
            image.seek(0)
            try:
                bot.createNewStickerSet(user_id=get_chat_creator(ctx.update.message.chat),
                                        name=create_pack_name(bot, ctx.update),
                                        title=f"{ctx.update.message.chat.title[:32]} by @{bot.getMe().username}",
                                        png_sticker=image,
                                        emojis=emoji)
            except BadRequest as e:
                if str(e).lower() == "peer_id_invalid":
                    return ctx.relpy(
                        ctx.localize(
                            "Sorry, but I can't create group pack right now. Ask group creator to PM me and try again."),
                        failed=True)
        sticker = bot.getStickerSet(create_pack_name(bot, ctx.update)).stickers[-1]
        return ctx.update.message.reply_sticker(sticker.file_id)
    except TimedOut:
        return ctx.reply(
            ctx.localize("It seems like I got timed out when creating sticker, that is Telegram-side error. Please try again."),
            failed=True)


@octobot.CommandHandler("pack_add", octobot.localizable("Adds sticker to personal stickerpack"), inline_support=False)
def sticker_add(bot, ctx):
    args = ctx.args
    if len(args) > 0:
        emoji = args[0]
    else:
        emoji = "🤖"
    try:
        try:
            image = resize_sticker(get_file_from_message(bot, ctx.update))
        except NoImageProvided:
            return ctx.reply(ctx.localize("No image as photo/file provided."), failed=True)
        except OverflowError:
            return ctx.reply(ctx.localize("Failed to compress image after 8 tries"), failed=True)
        except Image.DecompressionBombError:
            return ctx.reply(ctx.localize("Attempting to make image bombs, are we?"), failed=True)
        except OSError:
            return ctx.reply(ctx.localize("This file doesn't look like image file"), failed=True)
        try:
            bot.addStickerToSet(user_id=ctx.update.message.from_user.id,
                                name=create_pack_name(bot, ctx.update, personal=True),
                                png_sticker=image,
                                emojis=emoji)
        except BadRequest:
            image.seek(0)
            bot.createNewStickerSet(user_id=ctx.update.message.from_user.id,
                                    name=create_pack_name(bot, ctx.update, personal=True),
                                    title=f"{ctx.update.message.from_user.full_name[:32]} by @{bot.getMe().username}",
                                    png_sticker=image,
                                    emojis=emoji)
        sticker = bot.getStickerSet(create_pack_name(bot, ctx.update, personal=True)).stickers[-1]
        return ctx.update.message.reply_sticker(sticker.file_id)
    except TimedOut:
        return ctx.reply(
            ctx.localize("It seems like I got timed out when creating sticker, that is Telegram-side error. Please try again."),
            failed=True)
