from __future__ import annotations

from collections import defaultdict
from itertools import permutations, product

from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position


class AssignmentIterator:
    """Generates category-aware one-to-one assignments."""

    def iterate(self, items: list[Item]):
        groups: dict[str, list[Item]] = defaultdict(list)
        for item in items:
            groups[getattr(item, "category_id", "children")].append(item)

        if len(groups) <= 1:
            positions = [Position(i + 1) for i in range(len(items))]
            for permutation in permutations(positions):
                yield Assignment(dict(zip(items, permutation, strict=True)))
            return

        position_cache = {
            category_id: [Position(i + 1) for i in range(len(category_items))]
            for category_id, category_items in groups.items()
        }
        per_category = []
        for category_id, category_items in groups.items():
            per_category.append(
                [dict(zip(category_items, permutation, strict=True)) for permutation in permutations(position_cache[category_id])]
            )
        for combination in product(*per_category):
            merged = {}
            for partial in combination:
                merged.update(partial)
            yield Assignment(merged)
