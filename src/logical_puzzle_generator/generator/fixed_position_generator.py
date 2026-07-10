from __future__ import annotations

import random
from collections.abc import Iterable

from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.generator.difficulty import Difficulty
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.solution import Solution

from .solution_generator import SolutionGenerator


class FixedPositionGenerator:
    """Construct mandatory fixed-position anchors and a compatible solution."""

    def __init__(
        self,
        random_source: random.Random | None = None,
        solution_generator: SolutionGenerator | None = None,
    ) -> None:
        self._random = random_source if random_source is not None else random.Random()
        self._solution_generator = solution_generator

    def generate(
        self,
        items: Iterable[Item],
        difficulty: Difficulty,
    ) -> tuple[list[FixedPositionConstraint], Solution]:
        item_list = list(items)
        self._validate_items(item_list)

        required_count = self.required_count(difficulty)
        if required_count == 0 or len(item_list) < required_count:
            return [], self._solution_without_fixed_assignments(item_list)

        selected_items = self._random.sample(item_list, k=required_count)
        selected_positions = self._random.sample(
            [Position(index) for index in range(1, len(item_list) + 1)],
            k=required_count,
        )
        self._random.shuffle(selected_positions)

        assignment_by_item: dict[Item, Position] = dict(
            zip(selected_items, selected_positions, strict=True)
        )
        remaining_items = [item for item in item_list if item not in assignment_by_item]
        remaining_positions = [
            Position(index)
            for index in range(1, len(item_list) + 1)
            if Position(index) not in assignment_by_item.values()
        ]
        self._random.shuffle(remaining_items)
        self._random.shuffle(remaining_positions)
        assignment_by_item.update(dict(zip(remaining_items, remaining_positions, strict=True)))

        solution = Solution(Assignment(assignment_by_item))
        fixed_constraints = [
            FixedPositionConstraint(item, assignment_by_item[item]) for item in selected_items
        ]
        return fixed_constraints, solution

    def required_count(self, difficulty: Difficulty) -> int:
        if difficulty is Difficulty.EASY:
            return 2
        if difficulty is Difficulty.MEDIUM:
            return 1
        return 0

    def _solution_without_fixed_assignments(self, items: list[Item]) -> Solution:
        if self._solution_generator is not None:
            return self._solution_generator.generate(items)

        positions = [Position(index) for index in range(1, len(items) + 1)]
        self._random.shuffle(positions)
        return Solution(Assignment(dict(zip(items, positions, strict=True))))

    def _validate_items(self, items: list[Item]) -> None:
        if not items:
            raise ValueError("FixedPositionGenerator requires at least one item.")
        if any(not isinstance(item, Item) for item in items):
            raise TypeError("FixedPositionGenerator requires model.Item instances.")
        if len(set(items)) != len(items):
            raise ValueError("FixedPositionGenerator requires unique items.")
