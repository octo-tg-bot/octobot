import html

import telegram

import octobot
from octobot.dataclass import Suggestion
from settings import Settings
plugin = octobot.PluginInfo("Imgur")
if Settings.imgur_clientid == "":
    plugin.state = octobot.PluginStates.disabled
    plugin.state_description = "Imgur client ID is not set"
logger = plugin.logger


@octobot.catalogs.CatalogHandler("imgur", description=octobot.localizable("Search for image on Imgur"), suggestion=Suggestion(icon="https://s.imgur.com/images/favicon-152.png", title="Imgur", example_command="imgur cat"))
def imgur_search(query, index, max_count, bot: octobot.OctoBot, context: octobot.Context):
    index = int(index)
    page = index // 60
    start_pos = index % 60
    logger.debug("page %s, start pos %s", page, start_pos)
    if index < 0:
        raise octobot.catalogs.CatalogCantGoDeeper
    r = octobot.Database.get_cache(f"https://api.imgur.com/3/gallery/search/time/all/{page}", params={"q": query},
                                   headers={"Authorization": f"Client-ID {Settings.imgur_clientid}"}).json()
    if len(r["data"]) == 0:
        if index > 0:
            raise octobot.CatalogCantGoDeeper
        else:
            raise octobot.CatalogNotFound
    res = []
    for item in r["data"][start_pos:start_pos + max_count]:
        if "images" in item:
            photo = [octobot.CatalogPhoto(url=item["images"][0]["link"], width=item["images"][0]["width"],
                                          height=item["images"][0]["height"])]
        elif "gifv" in item:
            photo = [octobot.CatalogPhoto(
                url=item["gifv"], width=item["width"], height=item["height"])]
        elif "link" in item:
            photo = [octobot.CatalogPhoto(
                url=item["link"], width=item["width"], height=item["height"])]
        else:
            raise ValueError(f"Cant find image: {item}")
        text = [f'<b>{html.escape(item["title"])}</b>']
        if item["description"] is not None:
            text.append(context.localize("Description:"))
            text.append(f"<i>{html.escape(item['description'])}</i>")
        if "images_count" in item and item["images_count"] > 1:
            text.append(context.localize("Album with {count} images").format(
                count=item["images_count"]))
        res.append(octobot.CatalogKeyPhoto(item_id=item["id"],
                                           photo=photo,
                                           title=item["title"],
                                           text="\n".join(text),
                                           parse_mode="HTML",
                                           reply_markup=telegram.InlineKeyboardMarkup.from_button(telegram.InlineKeyboardButton(
                                               text=context.localize(
                                                   "View on Imgur"),
                                               url=item["link"]
                                           )))
                   )
    return octobot.Catalog(res, next_offset=index + max_count, current_index=index+1, previous_offset=index - max_count,
                           photo_primary=True)
