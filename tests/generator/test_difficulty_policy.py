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


def test_reduction_predicate_uses_exact_fixed_position_counts() -> None:
    mia, emma, lara, _ = items()
    policy = DifficultyPolicy()

    two = [FixedPositionConstraint(mia, Position(1)), FixedPositionConstraint(emma, Position(2))]
    one = [FixedPositionConstraint(mia, Position(1)), LeftOfConstraint(mia, emma)]
    zero = [LeftOfConstraint(mia, emma)]
    three = [*two, FixedPositionConstraint(lara, Position(3))]

    assert policy.can_remove_to_match(two, Difficulty.EASY)
    assert not policy.can_remove_to_match(one, Difficulty.EASY)
    assert policy.can_remove_to_match(one, Difficulty.MEDIUM)
    assert not policy.can_remove_to_match(two, Difficulty.MEDIUM)
    assert policy.can_remove_to_match(zero, Difficulty.HARD)
    assert not policy.can_remove_to_match(one, Difficulty.HARD)
    assert not policy.can_remove_to_match(three, Difficulty.EASY)


def test_required_fixed_position_count_is_owned_by_difficulty_policy() -> None:
    policy = DifficultyPolicy()

    assert policy.required_fixed_position_count(Difficulty.EASY) == 2
    assert policy.required_fixed_position_count("medium") == 1
    assert policy.required_fixed_position_count(Difficulty.HARD) == 0
