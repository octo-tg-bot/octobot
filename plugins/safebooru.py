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
import base64
import html
from dataclasses import dataclass
from urllib.parse import urlparse

import bs4
import requests
import telegram

import octobot
from octobot import CatalogPhoto, CatalogKeyArticle, Catalog, CatalogNotFound, OctoBot, Context, \
    localizable, PluginInfo, CatalogCantGoBackwards, CatalogKeyPhoto
from octobot.catalogs import CatalogHandler
MSG_TEMPLATE = localizable("""<b>Rating:</b> {rating}
<b>Tags:</b> {tags_str}""")

HEADERS = {"User-Agent": "OctoBot/1.0"}

MAX_RESULTS = 25

plugin = PluginInfo("Safebooru")


@dataclass
class SafebooruPost:
    id: int
    rating: int
    tags: [str]
    tags_str: str
    source: str
    file_url: str
    width: int
    height: int
    sample_url: str
    sample_width: int
    sample_height: int
    preview_url: str
    preview_width: int
    preview_height: int


@CatalogHandler(command=["safebooru", "sb"], description="Search posts on safebooru")
def safebooru_search(query: str, offset: str, limit: int, bot: OctoBot, ctx: Context) -> Catalog:
    res = []

    try:
        offset = int(offset)
    except ValueError:
        raise CatalogNotFound()

    if offset < 0:
        raise CatalogCantGoBackwards
    if offset // MAX_RESULTS > 0:
        iter_offset = offset % MAX_RESULTS
        page = offset // MAX_RESULTS
    else:
        page = 0
        iter_offset = offset
    if limit > MAX_RESULTS:
        limit = MAX_RESULTS
    plugin.logger.debug("iter offset %s, page %s", iter_offset, page)
    image = octobot.Database.get_cache("https://safebooru.org/index.php",
                         params={
                             "page": "dapi",
                             "s": "post",
                             "q": "index",
                             "tags": query,
                             "limit": MAX_RESULTS,
                             "pid": page
                         },
                         headers=HEADERS)
    api_q = bs4.BeautifulSoup(image.text, "html.parser").posts
    total = int(api_q.attrs["count"])

    if total == 0:
        raise CatalogNotFound()
    posts = api_q.find_all("post")
    plugin.logger.debug(posts)
    for post in posts[iter_offset:]:
        tags_base = html.escape(post.attrs["tags"]).split()
        tags = []
        tag_len = 0
        for tag in tags_base:
            if tag_len < 800:
                tags.append(f'<a href="{bot.generate_startlink("/sb " + tag)}">{tag}</a>')
                tag_len += len(tag)
            else:
                tags.append("<code>...</code>")
                break
        item = SafebooruPost(
            id=post.attrs["id"],
            rating=post.attrs["rating"],
            tags=tags,
            tags_str=" ".join(tags),
            source=post.attrs["source"],
            file_url=post.attrs["file_url"],
            width=int(post.attrs["width"]),
            height=int(post.attrs["height"]),
            sample_url=post.attrs["sample_url"],
            sample_width=int(post.attrs["sample_width"]),
            sample_height=int(post.attrs["sample_height"]),
            preview_url=post.attrs["preview_url"],
            preview_width=int(post.attrs["preview_width"]),
            preview_height=int(post.attrs["preview_height"]),
        )

        photos = [CatalogPhoto(url=item.sample_url,
                               width=item.sample_width,
                               height=item.sample_height),
                  CatalogPhoto(url=item.preview_url,
                               width=item.preview_width,
                               height=item.preview_height)]
        reply_markup = [
            [telegram.InlineKeyboardButton(
                url="https://safebooru.org/index.php?page=post&s=view&id={}".format(item.id),
                text=ctx.localize("View on safebooru")
            )]
        ]

        if item.source is not None:
            url = urlparse(item.source)
            if url.scheme in ["http", "https"]:
                reply_markup[0].append(telegram.InlineKeyboardButton(url=item.source, text=ctx.localize("Source")))

        res.append(CatalogKeyPhoto(text=ctx.localize(MSG_TEMPLATE).format(**item.__dict__),
                                   title="",
                                   description="",
                                   photo=photos,
                                   reply_markup=telegram.InlineKeyboardMarkup(reply_markup),
                                   parse_mode="HTML"))

    next_offset = offset + limit
    if next_offset > total:
        next_offset = None

    return Catalog(
        results=res,
        max_count=total,
        previous_offset=offset - limit,
        current_index=offset + 1,
        next_offset=next_offset,
        photo_primary=True
    )
