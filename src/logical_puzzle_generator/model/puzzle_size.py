from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PuzzleSize:
    """
    Size of one puzzle.
    """

    categories: int

    values_per_category: int

    @property
    def grid_size(self) -> int:
        return self.categories * self.values_per_category
