from __future__ import annotations

from logical_puzzle_generator.model.item import Item

from .base import Constraint


class SamePositionConstraint(Constraint):
    """Ensures two category items belong together by occupying the same position."""

    def __init__(self, first: Item, second: Item) -> None:
        if not isinstance(first, Item) or not isinstance(second, Item):
            raise TypeError("SamePositionConstraint operands must be Item instances.")
        if first == second:
            raise ValueError("SamePositionConstraint operands must be distinct items.")
        if first.category_id == second.category_id:
            raise ValueError("SamePositionConstraint operands must belong to different categories.")
        self.first = first
        self.second = second

    def matches(self, assignment) -> bool:
        return assignment.position_of(self.first) == assignment.position_of(self.second)

    @property
    def description(self) -> str:
        return f"{self.first} belongs with {self.second}"
