import json
import os
from glob import glob
import telegram
from babel.messages.pofile import read_po
import requests

BASE_ARGS = {"api_token": os.environ.get("POEDITOR_TOKEN", ""),
             "id": os.environ.get("POEDITOR_ID", "")}


def create_poeditor_catalog(catalog, endpoint):
    catalog_poeditor = []
    for message in catalog:
        msgid = message if isinstance(message, str) else message.id
        msgext = {}
        if not isinstance(message, str):
            msgext["translation"] = {"content": message.string}
            if not endpoint == "translations":
                msgext["reference"] = ""
                msgext["tags"] = []
                for location in message.locations:
                    msgext["reference"] += f"{location[0]}#{location[1]} "
                    msgext["tags"].append(location[0])
        if msgid != '':
            catalog_poeditor.append({
                "term": msgid,
                **msgext
            })
    return catalog_poeditor


def send_poeditor_catalog(endpoint, action, catalog, extra_args=None):
    if extra_args is None:
        extra_args = {}
    print(f"Uploading catalog to {endpoint}/{action}, args: {extra_args}")
    if not catalog:
        print("Nothing to send...")
        return {}
    catalog = json.dumps(create_poeditor_catalog(catalog, endpoint))
    r = requests.post(f"https://api.poeditor.com/v2/{endpoint}/{action}",
                      data={"data": catalog,
                            **BASE_ARGS,
                            **extra_args})
    r.raise_for_status()
    if r.json()["response"]["message"] != "OK":
        raise Exception(r.json()["response"]["message"])
    print("Result:", r.json()["result"])
    return r.json()["result"]


def sum_dict(x, y):
    """https://stackoverflow.com/a/10461916"""
    return {k: x.get(k, 0) + y.get(k, 0) for k in set(x) | set(y)}


def main():
    catalog_template = read_po(open('base.pot', encoding="utf-8"), domain="messages", ignore_obsolete=False)
    new_terms = send_poeditor_catalog("terms", "add", catalog=catalog_template)
    message = [f"Translation summary for {os.environ.get('GITHUB_SHA', 'COMMIT HASH HERE')}"]
    if new_terms['terms']['added'] > 0:
        message.append(f"🟢{new_terms['terms']['added']} new terms")

    deletions = {"deleted": 0}
    for language in glob("*/LC_MESSAGES/*.po"):
        catalog = read_po(open(language, encoding="utf-8"), domain="messages", ignore_obsolete=False)
        langcode = catalog.locale.language
        loc_msg = [f"Translation summary for language {langcode}"]
        new_translations = send_poeditor_catalog("translations", "add", catalog=catalog,
                                                 extra_args={"language": langcode})
        if "translations" in new_translations and new_translations["translations"]["added"] > 0:
            loc_msg.append(f"{new_translations['translations']['added']} terms translated")
        del_translations = send_poeditor_catalog("translations", "delete", catalog=catalog.obsolete,
                                                 extra_args={"language": langcode})
        if "translations" in del_translations and del_translations["translations"]["deleted"] > 0:
            loc_msg.append(f"{del_translations['translations']['deleted']} terms deleted")
        loc_tdel = send_poeditor_catalog("terms", "delete", catalog=catalog.obsolete)
        if "terms" in loc_tdel:
            deletions = sum_dict(deletions, loc_tdel["terms"])
        if len(loc_msg) > 1:
            message += loc_msg
    # Should be {}, but just in case
    overall_deletions = send_poeditor_catalog("terms", "delete", catalog=catalog_template.obsolete)
    if "terms" in overall_deletions:
        deletions = sum_dict(overall_deletions["terms"], deletions)
    if deletions["deleted"] > 0:
        message.insert(2, f"❌{deletions['deleted']} terms deleted")
    if len(message) == 1:
        message.append("No new or deleted terms")
    telegram.Bot(os.environ["TELEGRAM_TOKEN"]).sendMessage(os.environ["TELEGRAM_CHAT"], "\n".join(message))

if __name__ == '__main__':
    main()
