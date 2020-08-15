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


import calendar
import json
import re
import uuid
from math import ceil, floor
from typing import Callable, Any

import requests
from redis import Redis

from octobot import Database, Catalog, CatalogKeyArticle, OctoBot, Context, CatalogPhoto, CatalogNotFound
from octobot.handlers import CatalogHandler

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
    media (search: $query, type: $type) {
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
    characters (search: $query) {
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

MEDIA_TEMPLATE_STR = """
<b>{title}</b>
<i>{metadata}</i>
<a href="{siteUrl}">on anilist</a>

{description}

<i>{genres}</i>
"""

CHARACTER_TEMPLATE_STR = """
<b>{full_name}</b>
<i>{alternative_names}</i><a href="{siteUrl}">on anilist</a>

{description}

<i>Present in:</i>
{present_in}
"""

ANIME_MEDIA_STATUSES_STR = {
    "FINISHED": "finished",
    "RELEASING": "airing",
    "NOT_YET_RELEASED": "not yet airing",
    "CANCELLED": "cancelled"
}

MANGA_MEDIA_STATUSES_STR = {
    "FINISHED": "finished",
    "RELEASING": "releasing",
    "NOT_YET_RELEASED": "not yet released",
    "CANCELLED": "cancelled"
}

MEDIA_FORMAT_STR = {
    "TV": "TV animation series",
    "TV_SHORT": "TV short",
    "MOVIE": "anime movie",
    "SPECIAL": "anime special",
    "OVA": "OVA",
    "ONA": "ONA",
    "MUSIC": "AMV",
    "MANGA": "manga series",
    "NOVEL": "light novel series",
    "ONE_SHOT": "one-shot manga"
}

MEDIA_ANIME = "ANIME"
MEDIA_MANGA = "MANGA"

# TODO: add plugin name (AniList)


def cleanse_html(raw_html):
    r = re.compile("<.*?>")
    cleansed_text = re.sub(r, "", raw_html)
    cleansed_text = cleansed_text.replace('&', '&amp;')
    return cleansed_text


def cleanse_spoilers(raw_text):
    r = re.compile("~!.*!~", flags=re.S)
    cleansed_text = re.sub(r, "<i>(spoilers redacted)</i>", raw_text)
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


def get_fuzzy_date_str(fuzzy_date):
    year = fuzzy_date["year"]
    month = fuzzy_date["month"]
    day = fuzzy_date["day"]

    if day is not None:
        return f"{calendar.month_abbr[month]} {day}, {year}"
    elif month is not None:
        return f"{calendar.month_abbr[month]} {year}"
    elif year is not None:
        return str(year)
    else:
        return None


def get_media_metadata(media, ctx: Context):
    mtype = media["type"]
    metadata = []

    if media["format"] is not None and media["format"] in MEDIA_FORMAT_STR:
        metadata.append(MEDIA_FORMAT_STR[media["format"]])

    if media["status"] is not None:
        if mtype == MEDIA_ANIME:
            status_str = ctx.localize(ANIME_MEDIA_STATUSES_STR.get(media["status"], media["status"]))
        elif mtype == MEDIA_MANGA:
            status_str = ctx.localize(MANGA_MEDIA_STATUSES_STR.get(media["status"], media["status"]))
        metadata.append(status_str)

    if mtype == MEDIA_ANIME and media["episodes"] is not None:
        episodes_str = f"{media['episodes']} episodes"
        metadata.append(episodes_str)

    if mtype == MEDIA_MANGA:
        if media["volumes"] is not None:
            volumes_str = ctx.localize("{} volumes").format(media['volumes'])
            metadata.append(volumes_str)

        if media["chapters"] is not None:
            chapters_str = ctx.localize("{} chapters").format(media['chapters'])
            metadata.append(chapters_str)

    if media["averageScore"] is not None:
        score = media["averageScore"] / 10
        score_str = ctx.localize("rating {:0.1f}/10").format(score)
        metadata.append(score_str)

    if media["startDate"] is not None:
        start_date_str = get_fuzzy_date_str(media["startDate"])
        if start_date_str is not None:
            metadata.append(start_date_str)

    return metadata


def cached_catalog(fetch_fn, cache_key_fn, expires_after=60 * 60 * 60):
    def wrapper(fn):
        catalog_uuid = uuid.uuid4()

        def inner_wrapper(query: str, offset: str, limit: int, bot: OctoBot, ctx: Context, **kwargs) -> Catalog:
            # Only numeric offsets are supported for now
            try:
                offset = int(offset)
            except ValueError:
                raise CatalogNotFound()

            def cached_fetch_fn(query: str, offset: int, limit: int, **kwargs):
                if Database.redis is not None:
                    db: Redis = Database.redis
                    key_extra = cache_key_fn(query, **kwargs)
                    key = f"catalog:{catalog_uuid}:{key_extra}"
                    total_key = f"catalog:{catalog_uuid}:{key_extra}:total"

                    if not db.exists(key) or db.scard(key) < offset + limit:
                        items, total = fetch_fn(query, offset, limit, **kwargs)
                        db.expire(key, expires_after)
                        db.set(total_key, total)
                        db.expire(total, expires_after)
                        for item in items:
                            id = item["id"]
                            item_key = f"catalog:{catalog_uuid}:item:{id}"
                            db.set(item_key, json.dumps(item))
                            db.expire(item_key, expires_after)
                            db.sadd(key, id)
                        return items, total
                    else:
                        i = 0
                        items = []
                        for id in db.smembers(key):
                            if i < offset:
                                continue
                            elif i > offset + limit:
                                break
                            item_json = db.get(f"catalog:{catalog_uuid}:item:{id}")
                            item = json.loads(item_json)
                            items.append(item)
                        return items, db.get(total_key)
                else:
                    return fetch_fn(query, offset, limit, **kwargs)

            return fn(query, offset, limit, bot, ctx, fetch=cached_fetch_fn, **kwargs)

        return inner_wrapper

    return wrapper


def anilist_iter_media(query: str, offset: int, limit: int, media_type: str):
    resp = graphql(GRAPHQL_QUERY, "Media", {
        "query": query,
        "page": floor(offset / limit),
        "perPage": limit if offset % limit == 0 else limit * 2,
        "type": media_type
    })

    page_data = resp["data"]["Page"]
    page_info = page_data["pageInfo"]
    media = page_data["media"]

    total = page_info["total"]

    if total == 0:
        raise CatalogNotFound()

    return media, total


@cached_catalog(anilist_iter_media, lambda query, media_type: f"{query}:{media_type}")
def anilist_search_media(query, offset, count, bot: OctoBot, ctx: Context, fetch, media_type=MEDIA_ANIME):
    res = []

    # resp = graphql(GRAPHQL_QUERY, "Media", {
    #     "query": query,
    #     "page": ceil(offset / count),
    #     "perPage": count,
    #     "type": media_type
    # })

    media, total = fetch(query, offset, count, media_type=media_type)

    for item in media:
        item["title"] = get_media_title(item["title"])

        item["metadata"] = ", ".join(get_media_metadata(item, ctx))

        if item["description"] is not None:
            item["description"] = "<i>No description provided.</i>"
        else:
            item["description"] = cleanse_spoilers(cleanse_html(item["description"]))

        item["genres"] = ", ".join(item["genres"])

        text = ctx.localize(MEDIA_TEMPLATE_STR).format(**item)

        photos = [
            CatalogPhoto(url=item["coverImage"]["large"], width=0, height=0),
            CatalogPhoto(url=item["coverImage"]["medium"], width=0, height=0),
        ]

        res.append(CatalogKeyArticle(text=text, title=item["title"], photo=photos, parse_mode="HTML"))

    return Catalog(res, total)


@CatalogHandler(command=["anilist", "anime"], description="Search anime on AniList")
def anilist_search_anime(query, offset, count, bot, ctx):
    return anilist_search_media(query, offset, count, bot, ctx, media_type=MEDIA_ANIME)


@CatalogHandler(command=["anilist_manga", "manga"], description="Search manga on AniList")
def anilist_search_manga(query, offset, count, bot, ctx):
    return anilist_search_media(query, offset, count, bot, ctx, media_type=MEDIA_MANGA)


@CatalogHandler(command=["anilist_character", "anichar", "character"], description="Search for character on AniList")
def anilist_search_character(query: str, offset: str, limit: int, bot: OctoBot, ctx: Context) -> Catalog:
    res = []

    resp = graphql(GRAPHQL_QUERY, "Character", {
        "query": query,
        "page": ceil(int(offset) / limit),
        "perPage": limit
    })

    page_data = resp["data"]["Page"]
    page_info = page_data["pageInfo"]
    characters = page_data["characters"]

    total = page_info["total"]

    if total == 0:
        raise CatalogNotFound()

    for item in characters:
        item["full_name"] = item["name"]["full"]

        if len(item["name"]["alternative"]) > 0 and item["name"]["alternative"][0] != "":
            item["alternative_names"] = "aka " + ", ".join(item["name"]["alternative"]) + "\n"
        else:
            item["alternative_names"] = ""

        if item["description"] is not None:
            description = "<i>No description provided.</i>"
            item["description"] = f"<i>{description}</i>"
        else:
            description = item["description"] = cleanse_spoilers(cleanse_html(item["description"]))

        item["present_in"] = "\n".join(
            [f"<a href=\"{media['siteUrl']}\">{get_media_title(media['title'])}</a>" for media in
             item["media"]["nodes"]])

        text = ctx.localize(CHARACTER_TEMPLATE_STR).format(**item)

        photos = [
            CatalogPhoto(url=item["image"]["large"], width=0, height=0),
            CatalogPhoto(url=item["image"]["medium"], width=0, height=0),
        ]

        res.append(CatalogKeyArticle(text=text,
                                     title=item["full_name"],
                                     description=description,
                                     photo=photos,
                                     parse_mode="HTML"))

    return Catalog(res, total)
