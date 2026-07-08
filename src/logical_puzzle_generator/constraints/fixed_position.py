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
        return assignment.position_of(self.item) == self.position

    @property
    def description(self) -> str:
        return f"{self.item} stands at position {self.position}"
