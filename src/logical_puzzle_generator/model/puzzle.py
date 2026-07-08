from __future__ import annotations

from dataclasses import dataclass, field

from .category import Category
from .clue import Clue
from .metadata import Metadata
from .solution import Solution


@dataclass(slots=True)
class Puzzle:
    """
    Complete logical puzzle.
    """

    categories: list[Category]

    clues: list[Clue]

    solution: Solution

    metadata: Metadata

    difficulty: int = 1

    statistics: dict[str, int] = field(default_factory=dict)

    @property
    def clue_count(self) -> int:
        return len(self.clues)
