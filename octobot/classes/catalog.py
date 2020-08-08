import random
import string
from typing import Union, List
from dataclasses import dataclass


@dataclass
class CatalogPhoto:
    url: str
    width: int
    height: int


class CatalogKeyPhoto:
    def __init__(self, text: str, photo: Union[List[CatalogPhoto], CatalogPhoto], parse_mode: str = None,
                 title: str = None, item_id: str = None):
        self.item_id = item_id
        if self.item_id is None:
            self.item_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        self.text = text
        self.parse_mode = parse_mode
        self.title = title
        if isinstance(photo, str):
            photo = [photo]
        self.photo = photo


class CatalogKeyArticle:
    def __init__(self, text: str, photo: Union[List[CatalogPhoto], CatalogPhoto] = None, parse_mode: str = None,
                 title: str = None, item_id: str = None):
        self.item_id = item_id
        if self.item_id is None:
            self.item_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        self.text = text
        self.parse_mode = parse_mode
        self.title = title
        if isinstance(photo, CatalogPhoto):
            photo = [photo]
        self.photo = photo


class Catalog:
    def __init__(self, results: Union[List[CatalogKeyPhoto], List[CatalogKeyArticle]], max_count: int):
        self.results = results
        self.total_count = max_count

    def __iter__(self):
        return self.results.__iter__()

    def __getitem__(self, key):
        return self.results.__getitem__(key)


class CatalogCantGoDeeper(IndexError):
    pass
