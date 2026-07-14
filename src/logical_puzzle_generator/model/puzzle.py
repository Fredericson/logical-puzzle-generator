from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from copy import deepcopy
from types import MappingProxyType

from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.category import Category
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.metadata import Metadata
from logical_puzzle_generator.model.solution import Solution


@dataclass(slots=True)
class Puzzle:
    """
    Core puzzle model used by the solver, validator, generator, and PDF
    renderer.

    A puzzle consists of the items to place, the constraints that define the
    puzzle mathematically, and the human-readable clues shown to the user.
    """

    items: list[Item]

    constraints: list[Constraint]

    categories: list[Category] = field(default_factory=list)

    clues: list[Clue] = field(default_factory=list)

    metadata: Metadata | None = None

    solution: Solution | None = None

    fixed_positions: Mapping[Item, Position] = field(default_factory=dict)

    def __post_init__(self) -> None:
        fixed_positions = dict(self.fixed_positions)
        self._validate_fixed_positions(fixed_positions)
        self.fixed_positions = MappingProxyType(fixed_positions)

    def _validate_fixed_positions(self, fixed_positions: dict[Item, Position]) -> None:
        if not fixed_positions:
            return
        logical_items = self.logical_items
        logical_item_set = set(logical_items)
        if len(logical_item_set) != len(logical_items):
            raise ValueError(
                "Puzzle logical items must be unique when fixed positions are supplied."
            )
        for item, position in fixed_positions.items():
            if not isinstance(item, Item):
                raise TypeError("Fixed position keys must be Item instances.")
            if not isinstance(position, Position):
                raise TypeError("Fixed position values must be Position instances.")
            if item not in logical_item_set:
                raise ValueError("Fixed position item is not part of the puzzle logical items.")
            if item.category_id != CHILDREN_CATEGORY_ID:
                raise ValueError("Fixed positions may only be supplied for child items.")
        by_category: dict[str, list[Item]] = {}
        for item in logical_items:
            by_category.setdefault(item.category_id, []).append(item)
        used_by_category: dict[str, set[int]] = {}
        for item, position in fixed_positions.items():
            category_size = len(by_category[item.category_id])
            if position.index < 1 or position.index > category_size:
                raise ValueError("Fixed position index is outside the item category size.")
            used = used_by_category.setdefault(item.category_id, set())
            if position.index in used:
                raise ValueError("Fixed positions contain duplicate positions in one category.")
            used.add(position.index)
            if self.solution is not None and self.solution.assignment.position_of(item) != position:
                raise ValueError("Fixed positions must agree with the puzzle solution.")

    def __deepcopy__(self, memo):
        return Puzzle(
            items=deepcopy(self.items, memo),
            constraints=deepcopy(self.constraints, memo),
            categories=deepcopy(self.categories, memo),
            clues=deepcopy(self.clues, memo),
            metadata=deepcopy(self.metadata, memo),
            solution=deepcopy(self.solution, memo),
            fixed_positions=dict(self.fixed_positions),
        )

    @property
    def logical_items(self) -> list[Item]:
        if self.categories:
            return [item for category in self.categories for item in category.items]
        return list(self.items)
