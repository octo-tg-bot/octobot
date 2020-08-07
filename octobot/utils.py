def add_photo_to_text(text, photo_url):
    if isinstance(photo_url, str):
        photo_url = [photo_url]
    photos = ""
    for photo in photo_url:
        photos += f'<a href="{photo}">\u200b</a>'
    text = photos + text
    return text