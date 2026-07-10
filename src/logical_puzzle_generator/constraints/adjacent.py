from __future__ import annotations

from logical_puzzle_generator.model.item import Item

from .base import Constraint


class AdjacentConstraint(Constraint):
    """
    Ensures that two items are positioned next to each other.
    """

    def __init__(
        self,
        first: Item,
        second: Item,
    ) -> None:

        self.first = first
        self.second = second

    def matches(
        self,
        assignment,
    ) -> bool:

        first_position = assignment.position_of(self.first)
        second_position = assignment.position_of(self.second)

        if hasattr(first_position, "index"):
            first_position = first_position.index

        if hasattr(second_position, "index"):
            second_position = second_position.index

        return abs(first_position - second_position) == 1

    @property
    def description(self) -> str:

        return (
            f"{self.first} stands next to {self.second}"
        )
