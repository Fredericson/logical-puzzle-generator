from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position


@dataclass(frozen=True, slots=True)
class Assignment:
    """
    Complete assignment of all puzzle items.

    Example
    -------

    Lara -> Position(1)
    Mia  -> Position(3)
    Tim  -> Position(2)
    Noah -> Position(4)
    """

    positions: dict[Item, Position]

    def position_of(self, item: Item) -> Position:
        return self.positions[item]

    def contains(self, item: Item) -> bool:
        return item in self.positions

    def items(self) -> Iterator[Item]:
        return iter(self.positions.keys())

    def values(self) -> Iterator[Position]:
        return iter(self.positions.values())

    def __len__(self) -> int:
        return len(self.positions)
