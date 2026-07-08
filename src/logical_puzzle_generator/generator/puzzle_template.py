from __future__ import annotations

from dataclasses import dataclass

from logical_puzzle_generator.model.category import Category


@dataclass(slots=True)
class PuzzleTemplate:
    """
    Defines the static data used to generate one puzzle.
    """

    title: str

    theme: str

    categories: list[Category]

    @property
    def players(self) -> Category:
        """
        Returns the first category.

        Version 1.0 always uses the first category as the
        permutation source.
        """
        return self.categories[0]

    @property
    def item_count(self) -> int:
        return len(self.players.items)
