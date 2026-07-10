from __future__ import annotations

from logical_puzzle_generator.constraints import FixedPositionConstraint, LeftOfConstraint
from logical_puzzle_generator.generator import Difficulty, DifficultyPolicy
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position


def items() -> tuple[Item, Item, Item, Item]:
    return (Item("Mia"), Item("Emma"), Item("Lara"), Item("Aurelia"))


def test_two_fixed_position_constraints_are_easy() -> None:
    mia, emma, *_ = items()
    assert DifficultyPolicy().classify([
        FixedPositionConstraint(mia, Position(1)),
        FixedPositionConstraint(emma, Position(4)),
    ]) is Difficulty.EASY


def test_three_fixed_position_constraints_are_invalid_for_version_1() -> None:
    mia, emma, lara, _ = items()
    try:
        DifficultyPolicy().metadata_value([
            FixedPositionConstraint(mia, Position(1)),
            FixedPositionConstraint(emma, Position(2)),
            FixedPositionConstraint(lara, Position(4)),
        ])
    except ValueError as exc:
        assert "Invalid Version 1 fixed-position clue count 3" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_exactly_one_fixed_position_constraint_is_medium() -> None:
    mia, emma, *_ = items()
    assert DifficultyPolicy().classify([
        FixedPositionConstraint(mia, Position(1)),
        LeftOfConstraint(mia, emma),
    ]) is Difficulty.MEDIUM


def test_zero_fixed_position_constraints_are_hard() -> None:
    mia, emma, *_ = items()
    assert DifficultyPolicy().classify([LeftOfConstraint(mia, emma)]) is Difficulty.HARD


def test_direct_relations_do_not_count_as_fixed_position_clues() -> None:
    mia, emma, lara, _ = items()
    assert DifficultyPolicy().classify([
        LeftOfConstraint(mia, emma),
        LeftOfConstraint(emma, lara),
    ]) is Difficulty.HARD


def test_invalid_difficulty_fails_clearly() -> None:
    try:
        DifficultyPolicy().normalize("beginner")
    except ValueError as exc:
        assert "Unsupported difficulty" in str(exc)
        assert "easy, medium, hard" in str(exc)
    else:
        raise AssertionError("expected ValueError")
