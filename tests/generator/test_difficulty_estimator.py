from __future__ import annotations

from logical_puzzle_generator.constraints import (
    AdjacentConstraint,
    DirectLeftOfConstraint,
    DirectRightOfConstraint,
    FixedPositionConstraint,
    LeftOfConstraint,
    RightOfConstraint,
)
from logical_puzzle_generator.generator import DifficultyEstimator
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position


def items():
    return [Item("Mia"), Item("Emma"), Item("Lara"), Item("Aurelia")]


def test_anchor_plus_direct_relations_is_easy() -> None:
    mia, emma, lara, aurelia = items()
    difficulty = DifficultyEstimator().estimate(
        [
            FixedPositionConstraint(mia, Position(1)),
            DirectRightOfConstraint(emma, mia),
            DirectLeftOfConstraint(lara, aurelia),
        ]
    )

    assert difficulty == 1


def test_far_right_anchor_with_straightforward_direct_deduction_is_easy() -> None:
    mia, emma, lara, aurelia = items()
    difficulty = DifficultyEstimator().estimate(
        [
            FixedPositionConstraint(aurelia, Position(4)),
            DirectLeftOfConstraint(mia, emma),
            DirectLeftOfConstraint(emma, lara),
        ]
    )

    assert difficulty == 1


def test_exact_middle_position_counts_as_easy_anchor() -> None:
    mia, emma, lara, _aurelia = items()
    difficulty = DifficultyEstimator().estimate(
        [
            FixedPositionConstraint(emma, Position(3)),
            DirectLeftOfConstraint(mia, lara),
        ]
    )

    assert difficulty == 1


def test_no_anchor_but_direct_relation_is_medium() -> None:
    mia, emma, *_ = items()

    assert DifficultyEstimator().estimate([DirectRightOfConstraint(emma, mia)]) == 2


def test_direct_relation_and_adjacency_without_anchor_is_medium() -> None:
    mia, emma, lara, _ = items()
    difficulty = DifficultyEstimator().estimate(
        [DirectRightOfConstraint(emma, mia), AdjacentConstraint(emma, lara)]
    )

    assert difficulty == 2


def test_anchor_plus_several_ambiguous_relations_is_medium() -> None:
    mia, emma, lara, aurelia = items()
    difficulty = DifficultyEstimator().estimate(
        [
            FixedPositionConstraint(mia, Position(1)),
            AdjacentConstraint(emma, lara),
            LeftOfConstraint(emma, aurelia),
            RightOfConstraint(aurelia, lara),
        ]
    )

    assert difficulty == 2


def test_only_weak_relations_are_hard() -> None:
    mia, emma, lara, aurelia = items()
    difficulty = DifficultyEstimator().estimate(
        [
            LeftOfConstraint(mia, emma),
            RightOfConstraint(aurelia, lara),
        ]
    )

    assert difficulty == 3


def test_no_anchor_with_multiple_weak_relatives_is_hard() -> None:
    mia, emma, lara, aurelia = items()
    difficulty = DifficultyEstimator().estimate(
        [
            LeftOfConstraint(mia, emma),
            LeftOfConstraint(lara, aurelia),
            RightOfConstraint(aurelia, mia),
        ]
    )

    assert difficulty == 3


def test_no_anchor_with_ambiguous_adjacency_heavy_deduction_is_hard() -> None:
    mia, emma, lara, aurelia = items()
    difficulty = DifficultyEstimator().estimate(
        [
            AdjacentConstraint(mia, emma),
            AdjacentConstraint(emma, lara),
            AdjacentConstraint(lara, aurelia),
        ]
    )

    assert difficulty == 3


def test_regression_three_relative_clues_are_not_easy() -> None:
    mia, emma, lara, aurelia = items()
    difficulty = DifficultyEstimator().estimate(
        [
            DirectRightOfConstraint(emma, mia),
            AdjacentConstraint(emma, lara),
            RightOfConstraint(aurelia, emma),
        ]
    )

    assert difficulty in {2, 3}
