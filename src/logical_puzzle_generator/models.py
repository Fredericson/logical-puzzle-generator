from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from logical_puzzle_generator.model.category import Category
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.puzzle import Puzzle


class CategoryType(str, Enum):
    PERSON = "person"
    ATTRIBUTE = "attribute"


@dataclass(slots=True)
class PuzzleConfig:
    players: int = 4


__all__ = [
    "Category",
    "CategoryType",
    "Item",
    "Puzzle",
    "PuzzleConfig",
]
