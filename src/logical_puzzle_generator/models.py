from __future__ import annotations

from dataclasses import dataclass, field

from logical_puzzle_generator.model.category import Category, CategoryType
from logical_puzzle_generator.model.item import Item


@dataclass(slots=True)
class PuzzleConfig:
    """Compatibility configuration object for legacy puzzle model imports."""

    players: int = 4


@dataclass(slots=True)
class Puzzle:
    """Compatibility puzzle container for legacy ``logical_puzzle_generator.models`` imports."""

    categories: list[Category]
    config: PuzzleConfig = field(default_factory=PuzzleConfig)


__all__ = ["Category", "CategoryType", "Item", "Puzzle", "PuzzleConfig"]
