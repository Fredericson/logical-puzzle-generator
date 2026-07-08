from __future__ import annotations

from itertools import permutations

from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position


class AssignmentIterator:
    """
    Generates every possible assignment.

    For four players this yields 24 assignments.
    """

    def iterate(
        self,
        items: list[Item],
    ):

        positions = [
            Position(i + 1)
            for i in range(len(items))
        ]

        for permutation in permutations(positions):

            yield Assignment(
                dict(
                    zip(
                        items,
                        permutation,
                    )
                )
            )
