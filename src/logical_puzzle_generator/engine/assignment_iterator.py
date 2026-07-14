from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from itertools import permutations, product

from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position


class AssignmentIterator:
    """Generates category-aware one-to-one assignments."""

    def iterate(self, items: list[Item], fixed_positions: Mapping[Item, Position] | None = None):
        fixed_positions = fixed_positions or {}
        groups: dict[str, list[Item]] = defaultdict(list)
        for item in items:
            groups[getattr(item, "category_id", CHILDREN_CATEGORY_ID)].append(item)

        self._validate_fixed_positions(groups, fixed_positions)

        per_category = [
            self._category_assignments(category_items, fixed_positions)
            for category_items in groups.values()
        ]
        for combination in product(*per_category):
            merged = {}
            for partial in combination:
                merged.update(partial)
            yield Assignment(merged)

    def _category_assignments(
        self, category_items: list[Item], fixed_positions: Mapping[Item, Position]
    ) -> list[dict[Item, Position]]:
        positions = [Position(i + 1) for i in range(len(category_items))]
        fixed_for_category = {
            item: position for item, position in fixed_positions.items() if item in category_items
        }
        fixed_items = set(fixed_for_category)
        fixed_position_indexes = {position.index for position in fixed_for_category.values()}
        remaining_items = [item for item in category_items if item not in fixed_items]
        remaining_positions = [
            position for position in positions if position.index not in fixed_position_indexes
        ]
        assignments: list[dict[Item, Position]] = []
        for permutation in permutations(remaining_positions):
            candidate = dict(fixed_for_category)
            candidate.update(dict(zip(remaining_items, permutation, strict=True)))
            assignments.append(candidate)
        return assignments

    def _validate_fixed_positions(
        self, groups: dict[str, list[Item]], fixed_positions: Mapping[Item, Position]
    ) -> None:
        if not fixed_positions:
            return
        all_items = {item for category_items in groups.values() for item in category_items}
        if len(all_items) != sum(len(category_items) for category_items in groups.values()):
            raise ValueError("Assignment items must be unique when fixed positions are supplied.")
        for item, position in fixed_positions.items():
            if not isinstance(item, Item):
                raise TypeError("Fixed position keys must be Item instances.")
            if not isinstance(position, Position):
                raise TypeError("Fixed position values must be Position instances.")
            if item not in all_items:
                raise ValueError("Fixed position item is not part of the assignment items.")
        used_by_category: dict[str, set[int]] = {}
        for item, position in fixed_positions.items():
            category_items = groups[item.category_id]
            if position.index < 1 or position.index > len(category_items):
                raise ValueError("Fixed position index is outside the item category size.")
            used = used_by_category.setdefault(item.category_id, set())
            if position.index in used:
                raise ValueError("Fixed positions contain duplicate positions in one category.")
            used.add(position.index)
