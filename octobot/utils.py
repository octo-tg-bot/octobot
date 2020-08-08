from octobot.classes.catalog import CatalogPhoto


def add_photo_to_text(text, photo_url):
    if not isinstance(photo_url, list):
        photo_url = [photo_url]
    photos = ""
    for photo in photo_url:
        if isinstance(photo, CatalogPhoto):
            photo = photo.url
        photos += f'<a href="{photo}">\u200b</a>'
    text = photos + text
    return text


def path_to_module(path: str):
    return path.replace("\\", "/").replace("/", ".").replace(".py", "")