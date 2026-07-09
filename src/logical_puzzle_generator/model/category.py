from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .item import Item


class CategoryType(str, Enum):
    PERSON = "person"
    ATTRIBUTE = "attribute"


@dataclass(slots=True)
class Category:
    """
    One category inside a logical puzzle.

    Example

    Players

    Colours

    Drinks

    Animals
    """

    name: str
    items: list[Item]
    type: CategoryType | None = None

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)
