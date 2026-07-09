from __future__ import annotations

from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position

from .base import Constraint


class FixedPositionConstraint(Constraint):
    """
    Ensures that an item is located at a fixed position.
    """

    def __init__(
        self,
        item: Item,
        position: Position,
    ) -> None:
        self.item = item
        self.position = position

    def matches(
        self,
        assignment,
    ) -> bool:
        actual = assignment.position_of(self.item)
        expected = self.position

        if hasattr(actual, "index") and not hasattr(expected, "index"):
            return actual.index == expected

        if hasattr(expected, "index") and not hasattr(actual, "index"):
            return actual == expected.index

        return actual == expected

    @property
    def description(self) -> str:
        return f"{self.item} stands at position {self.position}"
