import html
import re

import telegram

import octobot
from settings import Settings

CHARACTER_EMOJIS = {
    "bloodhound": "🔎",
    "gibraltar": "🛡",
    "lifeline": "💊",
    "pathfinder": "🧗‍♂️",
    "wraith": "🌀",
    "bangalore": "🚀",
    "caustic": "☣️",
    "mirage": "🏃‍♂️",
    "octane": "💉",
    "wattson": "⚡️",
    "crypto": "🕵️‍♂️",
    "revenant": "⚰️",
    "loba": "💰",
    "rampart": "🔫",
    "horizon": "🚀"
}

inf = octobot.PluginInfo(octobot.localizable("Apex Legends player stats"))

API_BASEURL = "https://api.mozambiquehe.re/bridge"

PREFERRED_FIELDS = {
    "kills": octobot.localizable("Kills"),
    "damage": octobot.localizable("Damage"),
    "revives": octobot.localizable("Revives"),
    "games_played": octobot.localizable("Games player"),
    "kd": octobot.localizable("Kill/Death ratio")
}


def good_username(strg, search=re.compile(r'[^a-zA-Z\-_0-9 ]').search):
    return not bool(search(strg))


def get_apex_stats(platform, username, context):
    if good_username(username):
        res = octobot.Database.get_cache(API_BASEURL, params={
            "version": "4",
            "platform": platform.upper(),
            "player": username,
            "auth": Settings.mozamibque_here_token
        })
        status_code = res.status_code
        res = res.json()
        if status_code != 200:
            context.reply(context.localize(
                "Can't find player {}").format(username))
            return
        if "Error" in res:
            context.reply(context.localize(
                "Mozambiquehe.re API returned error: {}").format(res["Error"]))
            return
        player_info = [
            context.localize("Player <b>{username}</b>, level {level}").format(username=html.escape(username),
                                                                               level=res["global"]["level"])]
        if "rank" in res["global"]:
            player_info.append(context.localize(
                "Rank {rankName} {rankDiv}").format(**res["global"]["rank"]))
        selected_legend_name = res["legends"]["selected"]["LegendName"]
        player_info.append(context.localize("Current legend: <b>{}</b>").format(
            CHARACTER_EMOJIS.get(selected_legend_name.lower(
            ), "") + context.localize(selected_legend_name),

        ))
        for preferred_field, preferred_field_text in PREFERRED_FIELDS.items():
            if preferred_field in res["total"]:
                player_info.append(
                    "<b>{}</b> : {}".format(context.localize(preferred_field_text),
                                            res["total"][preferred_field]["value"]))
        kbd = [[telegram.InlineKeyboardButton(callback_data="nothing:", text=context.localize("Player legends stats"))],
               []]
        for legend_name, legend in res["legends"]["all"].items():
            text = [
                f"{CHARACTER_EMOJIS.get(legend_name.lower(), '')}{context.localize(legend_name)}"]
            if "data" not in legend:
                continue  # nothing interesting
            for stat in legend["data"]:
                text.append(f"{stat.get('name', 'key')}: {stat['value']}")
            text = '\n'.join(text)
            button = telegram.InlineKeyboardButton(
                text=CHARACTER_EMOJIS.get(
                    legend_name.lower(), '') + context.localize(legend_name),
                callback_data=f"popup_text:{text}")
            if len(kbd[-1]) >= 4:
                kbd.append([])
            kbd[-1].append(button)
        player_info.append(context.localize(
            "Powered by ApexLegendsStatus API"))
        context.reply("\n".join(player_info), parse_mode="HTML",
                      photo_url=res["legends"]["selected"]["ImgAssets"]["banner"],
                      reply_markup=telegram.InlineKeyboardMarkup(kbd),
                      title=context.localize(
                          "Apex Legends {username} stats").format(username=username),
                      inline_description=context.localize("Level {level}, ranked level {ranked_level}\nCurrent legend:{current_legend}").format(
                          level=res["global"]["level"],
                          ranked_level="{rankName} {rankDiv}".format(
                              **res["global"]["rank"]),
                          current_legend=context.localize(selected_legend_name)
        ))
    else:
        context.reply(context.localize("Invalid username specified!"))


CMD_DESCRIPTION = "Lookup Apex player on {}"


def create_handler(command, platform):
    @octobot.CommandHandler(command, description=CMD_DESCRIPTION.format(platform))
    def handler(bot, context):
        if len(context.args) > 0:
            return get_apex_stats(platform, context.query, context)
        else:
            context.reply(octobot.localizable("Specify username to lookup"))

    return handler


apex_pc_hnd = create_handler(["apex", "apex_pc"], "PC")
apex_ps4_hnd = create_handler(["apex_ps4"], "PS4")
apex_x1_hnd = create_handler(["apex_x1"], "X1")

# Command descriptions for localization system
octobot.localizable("Lookup Apex player on PC")
octobot.localizable("Lookup Apex player on PS4")
octobot.localizable("Lookup Apex player on X1")

# Character names for localization system
octobot.localizable("Bloodhound")
octobot.localizable("Gibraltar")
octobot.localizable("Lifeline")
octobot.localizable("Pathfinder")
octobot.localizable("Wraith")
octobot.localizable("Bangalore")
octobot.localizable("Caustic")
octobot.localizable("Mirage")
octobot.localizable("Octane")
octobot.localizable("Wattson")
octobot.localizable("Crypto")
octobot.localizable("Revenant")
octobot.localizable("Loba")
octobot.localizable("Rampart")
octobot.localizable("Horizon")
