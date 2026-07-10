from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.constraints import FixedPositionConstraint
from logical_puzzle_generator.generator import Difficulty, FixedPositionGenerator
from logical_puzzle_generator.model.item import Item


def items() -> list[Item]:
    return [Item("Aurelia"), Item("Emma"), Item("Lara"), Item("Mia")]


@pytest.mark.parametrize(
    ("difficulty", "expected_count"),
    [(Difficulty.EASY, 2), (Difficulty.MEDIUM, 1), (Difficulty.HARD, 0)],
)
def test_fixed_position_generator_returns_required_anchor_count(difficulty, expected_count) -> None:
    fixed_constraints, solution = FixedPositionGenerator(random.Random(3)).generate(
        items(), difficulty
    )

    assert len(fixed_constraints) == expected_count
    assert all(isinstance(constraint, FixedPositionConstraint) for constraint in fixed_constraints)
    assert all(constraint.matches(solution.assignment) for constraint in fixed_constraints)


def test_fixed_position_generator_easy_uses_distinct_items_and_positions() -> None:
    fixed_constraints, solution = FixedPositionGenerator(random.Random(12)).generate(
        items(), Difficulty.EASY
    )

    assert len({constraint.item for constraint in fixed_constraints}) == 2
    assert len({constraint.position for constraint in fixed_constraints}) == 2
    assert set(solution.positions) == set(items())
    assert {position.index for position in solution.positions.values()} == {1, 2, 3, 4}


def test_fixed_position_generator_varies_children_and_middle_positions_across_seeds() -> None:
    selected_children: set[str] = set()
    selected_positions: set[int] = set()

    for seed in range(1, 50):
        fixed_constraints, _solution = FixedPositionGenerator(random.Random(seed)).generate(
            items(), Difficulty.MEDIUM
        )
        assert len(fixed_constraints) == 1
        selected_children.add(fixed_constraints[0].item.name)
        selected_positions.add(fixed_constraints[0].position.index)

    assert len(selected_children) > 1
    assert selected_positions == {1, 2, 3, 4}
    assert {2, 3} <= selected_positions


def test_fixed_position_generator_is_seed_deterministic() -> None:
    first = FixedPositionGenerator(random.Random(21)).generate(items(), Difficulty.EASY)
    second = FixedPositionGenerator(random.Random(21)).generate(items(), Difficulty.EASY)

    first_constraints, first_solution = first
    second_constraints, second_solution = second

    assert [(c.item, c.position) for c in first_constraints] == [
        (c.item, c.position) for c in second_constraints
    ]
    assert first_solution.assignment == second_solution.assignment
