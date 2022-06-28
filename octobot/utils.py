import contextvars
import logging


current_context = contextvars.ContextVar('Current context data.')


def add_photo_to_text(text, photo_url):
    if not isinstance(photo_url, list):
        photo_url = [photo_url]
    photos = ""
    for photo in photo_url:
        # i hate fixing circular imports...
        if not isinstance(photo, str):
            photo = photo.url
        photos += f'<a href="{photo}">\u200b</a>'
    text = photos + text
    return text


def generate_edit_id(message):
    return f"emsg:{message.chat.id}:{message.message_id}"


def path_to_module(path: str):
    return path.replace("\\", "/").replace("/", ".").replace(".py", "")


class AddContextDataToLoggingRecord(logging.Filter):

    def filter(self, record):
        ctx: "octobot.Context" = current_context.get(None)
        if ctx is not None:
            record.update_type = type(ctx).__name__
            if ctx.chat:
                record.chat_name = ctx.chat.title
            record.called_command = ctx.called_command
        else:
            record.context_not_available = True
        return True
