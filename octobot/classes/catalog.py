import random
import string
from typing import Union, List, Any
from dataclasses import dataclass, field

import telegram


@dataclass
class CatalogPhoto:
    """
    :param url: URL to photo
    :type url: :class:`str`
    :param width: Photo width.
    :type width: :class:`int`
    :param height: Photo height.
    :type height: :class:`int`
    """
    url: str
    width: int = 100
    height: int = 100


class CatalogKeyArticle:
    """
    :param text: Text to include in result
    :type text: :class:`str`
    :param photo: Photo to include in text as preview and in inline mode as icon for result
    :type photo: :class:`CatalogPhoto` or class:`list` of :class:`CatalogPhoto`, optional
    :param parse_mode: Parse mode of messages. Become 'html' if `photo` is passed.
    :type parse_mode: :class:`str`, optional
    :param title: Item title for inline mode, defaults to first line of text
    :type title: :class:`str`, optional
    :param description: Description for inline mode, defaults to first 100 symbols of text
    :type description: :class:`str`, optional
    :param reply_markup: Inline keyboard that will appear in message
    :type reply_markup: :class:`telegram.InlineKeyboardMarkup`
    """

    def __init__(self, text: str, photo: Union[List[CatalogPhoto], CatalogPhoto] = None, parse_mode: str = None,
                 title: str = None, description: str = None, item_id: str = None,
                 reply_markup: telegram.InlineKeyboardMarkup = None):
        self.reply_markup = reply_markup
        if self.reply_markup is None:
            self.reply_markup = telegram.InlineKeyboardMarkup([])
        self.item_id = item_id
        if self.item_id is None:
            self.item_id = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=8))
        self.text = text
        self.parse_mode = parse_mode
        self.title = title
        if self.title is None:
            self.title = self.text.split("\n")[0][:40]
        self.description = description
        if self.description is None:
            self.description = self.text[:100]
        if isinstance(photo, CatalogPhoto):
            photo = [photo]
        self.photo = photo

    @property
    def photo_msgmode(self):
        if self.photo:
            photos = []
            for photo in self.photo:
                photos.append(photo.url)
            return photos

    @property
    def message(self):
        return {"text": self.text, "parse_mode": self.parse_mode, "reply_markup": self.reply_markup,
                "photo_url": self.photo_msgmode,
                "send_as_photo": type(self) == CatalogKeyPhoto}


class CatalogKeyPhoto(CatalogKeyArticle):
    """
    :param text: Text to include in result
    :type text: :class:`str`
    :param photo: Photo to include in text as preview and in inline mode
    :type photo: :class:`CatalogPhoto` or class:`list` of :class:`CatalogPhoto`, optional
    :param parse_mode: Parse mode of messages. Become 'html' if `photo` is passed.
    :type parse_mode: :class:`str`, optional
    :param title: Item title for inline mode, defaults to first line of text
    :type title: :class:`str`, optional
    :param description: Description for inline mode, defaults to first 100 symbols of text
    :type description: :class:`str`, optional
    """


@dataclass
class CatalogResult:
    results: List[CatalogKeyArticle] | List[CatalogKeyPhoto] = field(
        default_factory=list)
    current_index: Any = None
    next_offset: Any = None
    previous_offset: Any = None
    total: int = None
    query: str = "Anything written here will be overwritten by CatalogHelper."

    @property
    def __iter__(self):
        return self.results.__iter__

    @property
    def __getitem__(self):
        return self.results.__getitem__
