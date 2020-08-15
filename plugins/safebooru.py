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


from dataclasses import dataclass

import bs4
import requests

from octobot import CatalogHandler, CatalogPhoto, CatalogKeyArticle, Catalog, CatalogNotFound, OctoBot, Context

MSG_TEMPLATE = """<b>Rating:</b> %(rating)s
<b>Tags:</b> %(tags)s

<a href="%(file_url)s">open full-res image</a>, <a href="%(source)s">source</a>, <a href="https://safebooru.org/index.php?page=post&s=view&id=%(id)s">post on safebooru</a>"""

HEADERS = {"User-Agent": "OctoBot/1.0"}


# TODO: add plugin name (safebooru)

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

    image = requests.get("https://safebooru.org/index.php",
                         params={
                             "page": "dapi",
                             "s": "post",
                             "q": "index",
                             "tags": query,
                             "limit": limit,
                             "pid": int(offset) - 1
                         },
                         headers=HEADERS)
    api_q = bs4.BeautifulSoup(image.text, "html.parser").posts
    total = int(api_q.attrs["count"])

    if total == 0:
        raise CatalogNotFound()

    for post in api_q.find_all("post"):
        tags = post.attrs["tags"].split()[:1024]

        item = SafebooruPost(
            id=post.attrs["rating"],
            rating=post.attrs["rating"],
            tags=tags,
            tags_str=" ".join([f"<code>{tag}</code>" for tag in tags]),
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

        res.append(CatalogKeyArticle(text=ctx.localize(MSG_TEMPLATE).format(**item.__dict__),
                                     title=" ".join(item.tags),
                                     description="",
                                     photo=photos,
                                     parse_mode="HTML"))

    return Catalog(res, total)
