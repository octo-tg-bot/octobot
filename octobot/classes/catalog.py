import random
import string
from typing import Union, List
from dataclasses import dataclass

import telegram


@dataclass
class CatalogPhoto:
    """
    :param url: URL to photo
    :type url: :class:`str`
    :param width: Photo width. `Required due to Telegram Desktop bug <https://github.com/telegramdesktop/tdesktop/issues/4580>`_
    :type width: :class:`int`
    :param height: Photo height. `Required due to Telegram Desktop bug <https://github.com/telegramdesktop/tdesktop/issues/4580>`_
    :type height: :class:`int`
    """
    url: str
    width: int
    height: int


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
            self.item_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
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

@dataclass()
class Catalog:
    """
    Base catalog class

    :param results: Results found by function
    :type results: :class:`list` of :class:`CatalogKeyPhoto` or :class:`CatalogKeyArticle`
    :param max_count: Total amount of results function can return
    :type max_count: :class:`int`
    :param current_index: Current index
    :type current_index: :class:`int`
    :param next_offset: Next offset
    :type next_offset: :class:`str` or :class:`int`
    :param previous_offset: Previous offset
    :type previous_offset: :class:`str` or :class:`int`
    """
    results: Union[List[CatalogKeyPhoto], List[CatalogKeyArticle]]
    current_index: int
    next_offset: Union[str, int]
    current_index: int
    previous_offset: Union[str, int]
    max_count: Union[str, int] = "?"
    photo_primary: bool = False
    def __iter__(self):
        return self.results.__iter__()

    def __getitem__(self, key):
        return self.results.__getitem__(key)
