from __future__ import annotations

import random
from collections.abc import Iterable, Sequence

from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution

from .puzzle_template import PuzzleTemplate


class SolutionGenerator:
    """
    Creates random mathematically valid puzzle solutions.

    The generated solution is a complete one-to-one mapping from every
    source item to exactly one position. Version 1.0 uses the template's
    player category as the source category for the solution assignment.
    """

    def __init__(self, random_source: random.Random | None = None) -> None:
        self._random = random_source if random_source is not None else random.Random()

    def generate(
        self,
        source: PuzzleTemplate | Puzzle | Sequence[Item] | Iterable[Item],
    ) -> Solution:
        """
        Generate a random valid solution for the supplied items or template.

        Parameters
        ----------
        source:
            A ``PuzzleTemplate``, ``Puzzle``, or iterable of ``Item`` objects.
            Templates use their player category, while puzzles and iterables use
            their item collection directly.
        """
        items = self._items_from_source(source)
        self._validate_items(items)

        positions = [
            Position(index)
            for index in range(1, len(items) + 1)
        ]
        self._random.shuffle(positions)

        return Solution(
            Assignment(
                dict(
                    zip(
                        items,
                        positions,
                        strict=True,
                    )
                )
            )
        )

    def _items_from_source(
        self,
        source: PuzzleTemplate | Puzzle | Sequence[Item] | Iterable[Item],
    ) -> list[Item]:
        if isinstance(source, PuzzleTemplate):
            return list(source.players.items)

        if isinstance(source, Puzzle):
            return list(source.items)

        return list(source)

    def _validate_items(self, items: list[Item]) -> None:
        if not items:
            raise ValueError("A solution requires at least one item.")

        if any(not isinstance(item, Item) for item in items):
            raise TypeError("SolutionGenerator requires model.Item instances.")

        if len(set(items)) != len(items):
            raise ValueError("A solution requires unique items.")
