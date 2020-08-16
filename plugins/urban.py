import html

import requests
import telegram

import octobot
from octobot import catalogs
import textwrap
import re
apiurl = "http://api.urbandictionary.com/v0/define"

DEF_BASELINE = octobot.localizable("Definition for <b>{word}</b> by <i>{author}</i>:\n" + \
                                   "\n{definition}\n" + \
                                   "\nExample(s):\n" + \
                                   "{example}"
                                   )


def add_links(text: str, bot: octobot.OctoBot) -> str:
    matches = re.findall(r"\[.*?\]", text)
    for match in matches:
        query = match[1:-1]
        text = text.replace(match, f'<a href="{bot.generate_startlink("/ud " + query)}">{query}</a>')
    return text




@catalogs.CatalogHandler(["urban", "ud"], description="Urban dictionary search")
def urban_query(query, index, max_amount, bot: octobot.OctoBot, ctx: octobot.Context):
    index = int(index)
    if index == -1:
        return
    if index < 0:
        raise catalogs.CatalogCantGoBackwards
    r = requests.get(apiurl, params={"term": query}).json()
    if "list" in r and len(r["list"]) > 0:
        definitions = r["list"]
        if index > len(definitions):
            raise catalogs.CatalogCantGoDeeper
        res = []
        base = ctx.localize(DEF_BASELINE)
        text_link = ctx.localize("Definition on Urban Dictionary")
        for definition in definitions[index:max_amount + index]:
            desc_inline = textwrap.shorten(definition["definition"], width=100, placeholder="...")
            definition["definition"] = add_links(html.escape(definition["definition"]), bot)
            definition["example"] = add_links(html  .escape(definition["example"]), bot)
            definition["word"] = html.escape(definition["word"])
            definition["author"] = html.escape(definition["author"])
            res.append(catalogs.CatalogKeyArticle(title=ctx.localize("Definition for {}").format(definition["word"]),
                                                  description=desc_inline,
                                                  text=base.format(escape=html.escape, **definition),
                                                  parse_mode="html",
                                                  reply_markup=telegram.InlineKeyboardMarkup([[
                                                      telegram.InlineKeyboardButton(url=definition["permalink"],
                                                                                    text=text_link)
                                                  ]])))
        if index + max_amount > len(definitions):
            next_offset = -1
        else:
            next_offset = index + max_amount
        return catalogs.Catalog(res, max_count=len(definitions), current_index=index + 1, previous_offset=index - 1,
                                next_offset=next_offset)
    else:
        raise catalogs.CatalogNotFound
