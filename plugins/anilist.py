# The MIT License (MIT)
# Copyright (c) 2020 handlerug
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

import datetime
import re
import textwrap
from typing import Union

import babel.dates
import requests
import telegram

from octobot import Catalog, CatalogKeyArticle, OctoBot, Context, CatalogPhoto, CatalogNotFound, localizable, \
    PluginInfo, CatalogCantGoBackwards, CatalogCantGoDeeper, UpdateType, Database
from octobot.catalogs import CatalogHandler

GRAPHQL_URL = "https://graphql.anilist.co"

GRAPHQL_QUERY = """
query Media($query: String, $page: Int, $perPage: Int, $type: MediaType) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      perPage
      currentPage
      lastPage
      hasNextPage
    }
    media(search: $query, type: $type) {
      id
      type
      title {
        english
        romaji
      }
      format
      genres
      description
      status
      episodes
      volumes
      chapters
      coverImage {
        large
        medium
      }
      startDate {
        year
        month
        day
      }
      endDate {
        year
        month
        day
      }
      averageScore
      siteUrl
    }
  }
}

query Character($query: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      perPage
      currentPage
      lastPage
      hasNextPage
    }
    characters(search: $query) {
      id
      name {
        full
        alternative
      }
      image {
        large
        medium
      }
      description
      media {
        nodes {
          title {
            romaji
            english
          }
          siteUrl
        }
      }
      siteUrl
    }
  }
}
"""

ANIME_MEDIA_STATUSES_STR = {
    "FINISHED": localizable("finished"),
    "RELEASING": localizable("airing"),
    "NOT_YET_RELEASED": localizable("not yet airing"),
    "CANCELLED": localizable("cancelled")
}

MANGA_MEDIA_STATUSES_STR = {
    "FINISHED": localizable("finished"),
    "RELEASING": localizable("releasing"),
    "NOT_YET_RELEASED": localizable("not yet released"),
    "CANCELLED": localizable("cancelled")
}

MEDIA_FORMAT_STR = {
    "TV": localizable("TV animation series"),
    "TV_SHORT": localizable("TV short"),
    "MOVIE": localizable("anime movie"),
    "SPECIAL": localizable("anime special"),
    "OVA": localizable("OVA"),
    "ONA": localizable("ONA"),
    "MUSIC": localizable("AMV"),
    "MANGA": localizable("manga series"),
    "NOVEL": localizable("light novel series"),
    "ONE_SHOT": localizable("one-shot manga")
}

MEDIA_ANIME = "ANIME"
MEDIA_MANGA = "MANGA"

MAX_PER_PAGE = 50


plugin = PluginInfo("AniList")


def shorten(text: str, length: int):
    if len(text) > length:
        return text[:length-3] + "..." # "…" is also 3 bytes and looks the same, but less supported
    return text


def cleanse_html(raw_html):
    cleansed_text = re.sub("<.*?>", "", raw_html)
    # not necessary?
    # cleansed_text = cleansed_text.replace('&', '&amp;')
    return cleansed_text


def cleanse_spoilers(raw_text: str, replacement_text: str):
    r = re.compile("~!.*!~", flags=re.S)
    cleansed_text = re.sub(r, replacement_text, raw_text)
    return cleansed_text


def collapse_whitespace(text: str):
    return "\n".join([re.sub(" +", " ", line).strip() for line in text.split("\n")])


def get_media_title(title):
    romaji, english = title["romaji"], title["english"]

    if romaji == english or english is None:
        title_str = romaji
    else:
        title_str = f"{english} ({romaji})"

    return title_str


def get_fuzzy_date_str(fuzzy_date, ctx: Context):
    year = fuzzy_date["year"]
    month = fuzzy_date["month"]
    day = fuzzy_date["day"]

    if day is not None and month is not None and year is not None:
        return babel.dates.format_date(date=datetime.date(year, month, day), locale=ctx.locale)
    elif month is not None and year is not None:
        return f"{babel.dates.get_month_names(locale=ctx.locale)[month]} {year}"
    elif year is not None:
        return str(year)
    else:
        return None


def format_media_description(description: Union[str, None], ctx: Context):
    if description is None:
        description = ctx.localize("No description provided.")
    else:
        description = cleanse_html(description)
        description = collapse_whitespace(description)
        description = cleanse_spoilers(description, ctx.localize("(spoilers redacted)"))
        description = shorten(description, 1024)

    return description, description[:70]


def get_media_metadata(media, ctx: Context):
    mtype = media["type"]
    metadata = []

    if media["status"] is not None:
        if mtype == MEDIA_ANIME:
            status_str = ctx.localize(ANIME_MEDIA_STATUSES_STR.get(media["status"], media["status"]))
        elif mtype == MEDIA_MANGA:
            status_str = ctx.localize(MANGA_MEDIA_STATUSES_STR.get(media["status"], media["status"]))
        else:
            status_str = media['status']
        metadata.append("<b>{}:</b> {}".format(ctx.localize("status"), status_str))

    if mtype == MEDIA_ANIME and media["episodes"] is not None:
        metadata.append(ctx.nlocalize("{} episode", "{} episodes", media["episodes"]).format(media["episodes"]))

    if mtype == MEDIA_MANGA:
        if media["volumes"] is not None:
            metadata.append(ctx.nlocalize("{} volume", "{} volumes", media["volumes"]).format(media['volumes']))
        if media["chapters"] is not None:
            metadata.append(ctx.nlocalize("{} chapter", "{} chapters", media["chapters"]).format(media["chapters"]))

    if media["averageScore"] is not None:
        score = media["averageScore"] / 10
        metadata.append("<b>{}:</b> {:0.1f}/10".format(ctx.localize("rating"), score))

    if media["startDate"] is not None:
        end_date_str = get_fuzzy_date_str(media["startDate"], ctx)
        if end_date_str is not None:
            metadata.append("<b>{}:</b> {}".format(ctx.localize("first released on"), end_date_str))

    if media["endDate"] is not None:
        end_date_str = get_fuzzy_date_str(media["startDate"], ctx)
        if end_date_str is not None:
            metadata.append("<b>{}:</b> {}".format(ctx.localize("last released on"), end_date_str))

    return metadata


def anilist_command(operation_name: str, **kwargs):
    def wrapper(func):
        def handler(query: str, offset: str, count: int, bot: OctoBot, ctx: Context):
            if offset == 'None':
                raise CatalogCantGoDeeper

            try:
                offset = int(offset)
            except ValueError:
                raise CatalogNotFound

            if offset < 0:
                raise CatalogCantGoBackwards

            if count > MAX_PER_PAGE:
                count = MAX_PER_PAGE
            
            page = offset // MAX_PER_PAGE + 1

            r = Database.post_cache(GRAPHQL_URL, json={
                "query": GRAPHQL_QUERY,
                "operationName": operation_name,
                "variables": {
                    "query": query,
                    "page": page,
                    "perPage": MAX_PER_PAGE,
                    **kwargs,
                },
            })
            r.raise_for_status()
            resp = r.json()

            page_data = resp["data"]["Page"]

            page_info = page_data["pageInfo"]
            total = page_info["total"]
            current_page = page_info["currentPage"]
            last_page = page_info["lastPage"]

            if total == 0:
                raise CatalogNotFound

            res = func(page_data, bot, ctx)

            prev_offset = offset - count
            next_offset = offset + count
            if next_offset >= total:
                next_offset = None

            return Catalog(
                results=res[offset % MAX_PER_PAGE:],
                max_count=total,
                previous_offset=prev_offset,
                current_index=offset + 1,
                next_offset=next_offset
            )

        return handler

    return wrapper


@CatalogHandler(command="anilist", description=localizable("Search on AniList"))
@anilist_command("Media")
def anilist(page: dict, bot: OctoBot, ctx: Context) -> [CatalogKeyArticle]:
    media = page["media"]
    res = []

    for item in media:
        item["short_title"] = item["title"]["english"] or item["title"]["romaji"]
        item["title"] = get_media_title(item["title"])
        item["format"] = ctx.localize(MEDIA_FORMAT_STR.get(item["format"], item["format"]))

        item["metadata"] = "\n".join(get_media_metadata(item, ctx))
        item["description"], short_description = format_media_description(item["description"], ctx)
        item["genres"] = ", ".join(item["genres"])

        text = """<b>{title}</b>
<i>{format}</i>

{metadata}

{description}

<i>{genres}</i>
""".format(**item)

        photos = [
            CatalogPhoto(url=item["coverImage"]["large"], width=0, height=0),
            CatalogPhoto(url=item["coverImage"]["medium"], width=0, height=0),
        ]

        reply_markup = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton(
                url=item["siteUrl"],
                text=ctx.localize("View on AniList")
            )]
        ])

        res.append(CatalogKeyArticle(item_id=item["id"],
                                     title=f"{item['short_title']} ({item['format']})",
                                     description=short_description,
                                     text=text,
                                     photo=photos,
                                     reply_markup=reply_markup,
                                     parse_mode="HTML"))

    return res


@CatalogHandler(command="character", description=localizable("Search for characters on AniList"))
@anilist_command("Character")
def character(page: dict, bot: OctoBot, ctx: Context) -> [CatalogKeyArticle]:
    characters = page["characters"]
    res = []

    for item in characters:
        item["name"]["alternative"] = list(filter(lambda s: len(s.strip()), item["name"]["alternative"]))
        if len(item["name"]["alternative"]) > 0:
            item["alternative_names"] = "Also known as " + ", ".join(item["name"]["alternative"]) + "\n"
        else:
            item["alternative_names"] = ""

        item["description"], short_description = format_media_description(item["description"], ctx)

        item["present_in"] = "\n".join(
            ['<a href="{siteUrl}">{title}</a>'.format(siteUrl=media['siteUrl'], title=get_media_title(media['title'])) for media in
             item["media"]["nodes"]])

        text = """<b>{name[full]}</b>
{alternative_names}
{description}

<i>{present_in_title}:</i>
{present_in}
""".format(**item, present_in_title=ctx.localize("Present in"))

        photos = [
            CatalogPhoto(url=item["image"]["large"], width=0, height=0),
            CatalogPhoto(url=item["image"]["medium"], width=0, height=0),
        ]

        reply_markup = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton(
                url=item["siteUrl"],
                text=ctx.localize("View on AniList")
            )]
        ])

        res.append(CatalogKeyArticle(item_id=item["id"],
                                     title=item["name"]["full"],
                                     description=short_description,
                                     text=text,
                                     photo=photos,
                                     reply_markup=reply_markup,
                                     parse_mode="HTML"))

    return res
