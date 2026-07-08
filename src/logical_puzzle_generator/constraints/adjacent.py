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

        return (
            abs(
                assignment.position_of(self.first)
                - assignment.position_of(self.second)
            )
            == 1
        )

    @property
    def description(self) -> str:

        return (
            f"{self.first} stands next to {self.second}"
        )
