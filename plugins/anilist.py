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
    PluginInfo, CatalogCantGoBackwards, CatalogCantGoDeeper, UpdateType
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
HEADERS = {"User-Agent": "OctoBot/1.0"}

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

plugin = PluginInfo("AniList")


def cleanse_html(raw_html):
    r = re.compile("<.*?>")
    cleansed_text = re.sub(r, "", raw_html)
    cleansed_text = cleansed_text.replace('&', '&amp;')
    return cleansed_text


def cleanse_spoilers(raw_text: str, replacement_text: str):
    r = re.compile("~!.*!~", flags=re.S)
    cleansed_text = re.sub(r, replacement_text, raw_text)
    return cleansed_text


def graphql(query, operation_name, params):
    r = requests.post(GRAPHQL_URL, json={"query": query, "operationName": operation_name, "variables": params},
                      headers=HEADERS)
    r.raise_for_status()
    json = r.json()
    return json


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

    if day is not None:
        return babel.dates.format_date(date=datetime.date(year, month, day), locale=ctx.locale)
    elif month is not None:
        return f"{babel.dates.get_month_names(locale=ctx.locale)[month]} {year}"
    elif year is not None:
        return str(year)
    else:
        return None


def format_media_description(description: Union[str, None], ctx: Context):
    if description is None:
        short = ctx.localize("No description provided.")
        long = f"<i>{short}</i>"
    else:
        long = cleanse_html(description)
        replacement_text = ctx.localize("(spoilers redacted)")
        short = cleanse_spoilers(long, replacement_text)
        long = cleanse_spoilers(long, f"<i>{replacement_text}</i>")

    short = textwrap.shorten(short, width=70, placeholder="…")
    long = textwrap.shorten(long, width=1024, placeholder="…")

    return long, short


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


def anilist_command(query_name: str, **kwargs):
    def wrapper(func):
        def handler(query: str, offset: str, count: int, bot: OctoBot, ctx: Context):
            try:
                offset = int(offset)
            except ValueError:
                raise CatalogNotFound

            if offset < 0:
                raise CatalogCantGoBackwards

            defaults = {
                "query": query,
                "page": offset,
                "perPage": count
            }

            resp = graphql(GRAPHQL_QUERY, query_name, {
                **defaults,
                **kwargs,
            })

            page_data = resp["data"]["Page"]

            page_info = page_data["pageInfo"]
            total = page_info["total"]
            current_page = page_info["currentPage"]
            last_page = page_info["lastPage"]

            if total == 0:
                raise CatalogNotFound

            res = func(page_data, bot, ctx)
            if len(res) == 0:
                if ctx.update_type == UpdateType.inline_query:
                    return None
                else:
                    raise CatalogCantGoDeeper

            previous_offset = current_page - 1 if offset > 0 else -1

            return Catalog(
                results=res,
                max_count=last_page,
                previous_offset=previous_offset,
                current_index=current_page,
                next_offset=current_page + 1
            )

        return handler

    return wrapper


@CatalogHandler(command="anilist", description=localizable("Search on AniList"))
@anilist_command("Media")
def anilist(page: dict, bot: OctoBot, ctx: Context) -> [CatalogKeyArticle]:
    media = page["media"]
    res = []

    for item in media:
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

        res.append(CatalogKeyArticle(title=f"{item['title']} ({item['format']})",
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
        if len(item["name"]["alternative"]) > 0 and item["name"]["alternative"][0] != "":
            item["alternative_names"] = "Also known as " + ", ".join(item["name"]["alternative"]) + "\n"
        else:
            item["alternative_names"] = ""

        item["description"], short_description = format_media_description(item["description"], ctx)

        item["present_in"] = "\n".join(
            ['<a href="{siteUrl}">{title}</a>'.format(**media, title=get_media_title(media['title'])) for media in
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

        res.append(CatalogKeyArticle(title=item["full_name"],
                                     description=short_description,
                                     text=text,
                                     photo=photos,
                                     reply_markup=reply_markup,
                                     parse_mode="HTML"))

    return res
