from __future__ import annotations

from logical_puzzle_generator.model.item import Item

from .base import Constraint


class DirectLeftOfConstraint(Constraint):
    """
    Ensures that one item is positioned immediately left of another.
    """

    def __init__(self, left: Item, right: Item) -> None:
        self.left = left
        self.right = right

    def matches(self, assignment) -> bool:
        return (
            assignment.position_of(self.left).index + 1 == assignment.position_of(self.right).index
        )

    @property
    def description(self) -> str:
        return f"{self.left} stands directly left of {self.right}"
