from __future__ import annotations

from dataclasses import dataclass

from .item import Item


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

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)
