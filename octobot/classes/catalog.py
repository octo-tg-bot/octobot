import random
import string
from typing import Union, List, Any
from dataclasses import dataclass, field

import telegram
import logging
logger = logging.getLogger("catalog_class")


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
    def __init__(self, text: str, photo: Union[List[CatalogPhoto], CatalogPhoto] = None, parse_mode: str = None,
                 title: str = None, description: str = None, item_id: str = None,
                 reply_markup: telegram.InlineKeyboardMarkup = None):
        """Catalog key

        Args:
            text (str): Text to send
            photo (Union[List[CatalogPhoto], CatalogPhoto], optional): Photo to send. Defaults to None.
            parse_mode (str, optional): Telegram parse mode. Defaults to None.
            title (str, optional): Title in inline mode. Defaults to None.
            description (str, optional): Description in inline mode. Defaults to None.
            item_id (str, optional): Item unique id. Defaults to None.
            reply_markup (telegram.InlineKeyboardMarkup, optional): Reply markup. Defaults to None.
            context (Context, optional): Context. Defaults to None.
        """
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

    @property
    def inline(self):
        article = {"id": self.item_id,
                   "parse_mode": self.parse_mode,
                   "reply_markup": self.reply_markup,
                   "title": self.title,
                   "description": self.description}
        article["caption" if isinstance(
            self, CatalogKeyPhoto) else "text"] = self.text
        if self.photo is not None:
            article.update(dict(
                photo_url=self.photo[0].url,
                photo_width=self.photo[0].width,
                photo_height=self.photo[0].height,
                thumb_url=self.photo[-1].url,
            ))
        logger.debug(article)
        return article


class CatalogKeyPhoto(CatalogKeyArticle):
    pass


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
