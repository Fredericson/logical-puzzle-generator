from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CategoryType(Enum):
    PERSON = "person"
    POSITION = "position"
    COLOR = "color"


@dataclass(frozen=True)
class Item:
    name: str


@dataclass(frozen=True)
class Category:
    name: str
    type: CategoryType
    items: list[Item] = field(default_factory=list)


@dataclass(frozen=True)
class PuzzleConfig:
    theme: str = "tennis"
    difficulty: int = 2
    players: int = 4


@dataclass(frozen=True)
class Puzzle:
    categories: list[Category]
    config: PuzzleConfig
