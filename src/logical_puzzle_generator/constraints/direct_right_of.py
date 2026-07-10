from __future__ import annotations

from logical_puzzle_generator.model.item import Item

from .base import Constraint


class DirectRightOfConstraint(Constraint):
    """
    Ensures that one item is positioned immediately right of another.
    """

    def __init__(self, right: Item, left: Item) -> None:
        self.right = right
        self.left = left

    def matches(self, assignment) -> bool:
        return (
            assignment.position_of(self.right).index == assignment.position_of(self.left).index + 1
        )

    @property
    def description(self) -> str:
        return f"{self.right} stands directly right of {self.left}"
