# The MIT License (MIT)
# Copyright (c) 2019 OctoNezd
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

"""
Word swap module
"""
import html
import re2 as re
import string

import octobot

PLUGINVERSION = 2
from difflib import Differ


def appendCodeChanges(s1, s2):
    """
    Adds <b></b> tags to words that are changed
    https://stackoverflow.com/a/10775310
    """
    l1 = s1.split(' ')
    l2 = s2.split(' ')
    dif = list(Differ().compare(l1, l2))
    return " ".join(['<b>' + i[2:] + '</b>' if i[:1] == '+' else i[2:] for i in dif
                     if not i[:1] in '-?'])


# Always name this variable as `plugin`
# If you dont, module loader will fail to load the plugin!
plugin = octobot.PluginInfo(name=octobot.localizable("Word Swapper"))


@octobot.CommandHandler(command=["s/", "/s/"],
                        description=octobot.localizable("Swaps word(s) in message"),
                        prefix="",
                        inline_support=False)
def wordsw(bot, context):
    try:
        msg = context.update.message
        txt = msg.text
        if msg.reply_to_message is not None:
            if not msg.reply_to_message.from_user.id == bot.getMe().id:
                offset = (1 if txt.startswith("/") else 0)
                groups = [b.replace("\/", "/") for b in re.split(r"(?<!\\)/", txt)]
                find = groups[1 + offset]
                ready_for_replacement = False
                for letter in find:
                    if not letter in string.punctuation + " ":
                        ready_for_replacement = True
                if not ready_for_replacement:
                    print("not ready for replacement")
                    return
                replacement = groups[2 + offset]
                if len(groups) > 3+offset:
                    flags = groups[3+offset]
                else:
                    flags = ""
                find_re = re.compile("{}{}".format("(?{})".format(flags.replace("g", "")) if flags.replace("g", "") != "" else "", find))
                mod_msg = find_re.sub(replacement, msg.reply_to_message.text, count=100)
                if mod_msg == msg.reply_to_message.text:
                    # Nothing changed.
                    return
                mod_msg = appendCodeChanges(html.escape(msg.reply_to_message.text), html.escape(mod_msg))
                text = context.localize("Hi, {username}!\nDid you mean:\n{text}").format(username=msg.reply_to_message.from_user.mention_html(),
                                                                                         text=mod_msg)
                return context.reply(text=text, parse_mode="HTML", reply_to_previous=True)
    except IndexError:
        pass
    except re.error:
        return context.reply(text=context.localize("Invalid regex!"), failed=True)
    except AttributeError:
        return context.reply(text=context.localize("You should reply to message with text!"), failed=True)
