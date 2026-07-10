from __future__ import annotations

from logical_puzzle_generator.constraints import (
    AdjacentConstraint,
    DirectLeftOfConstraint,
    DirectRightOfConstraint,
    FixedPositionConstraint,
    LeftOfConstraint,
    RightOfConstraint,
)
from logical_puzzle_generator.generator import ConstraintDistributionPolicy
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position


def _items() -> tuple[Item, Item, Item, Item]:
    return Item("A"), Item("B"), Item("C"), Item("D")


def test_repeated_left_of_constraints_are_penalized() -> None:
    a, b, c, d = _items()
    policy = ConstraintDistributionPolicy()

    repeated = [LeftOfConstraint(a, b), LeftOfConstraint(a, c), LeftOfConstraint(a, d)]
    varied = [LeftOfConstraint(a, b), DirectRightOfConstraint(c, b), AdjacentConstraint(c, d)]

    assert policy.score(varied) > policy.score(repeated)
    assert not policy.accepts(repeated, "hard")


def test_repeated_right_of_constraints_are_penalized() -> None:
    a, b, c, d = _items()
    policy = ConstraintDistributionPolicy()

    repeated = [RightOfConstraint(b, a), RightOfConstraint(c, a), RightOfConstraint(d, a)]
    varied = [RightOfConstraint(b, a), DirectLeftOfConstraint(b, c), AdjacentConstraint(c, d)]

    assert policy.score(varied) > policy.score(repeated)
    assert not policy.accepts(repeated, "hard")


def test_repeated_adjacent_constraints_are_penalized() -> None:
    a, b, c, d = _items()
    policy = ConstraintDistributionPolicy()

    repeated = [AdjacentConstraint(a, b), AdjacentConstraint(b, c), AdjacentConstraint(c, d)]
    varied = [AdjacentConstraint(a, b), DirectLeftOfConstraint(b, c), RightOfConstraint(d, a)]

    assert policy.score(varied) > policy.score(repeated)
    assert not policy.accepts(repeated, "medium")


def test_diversity_bonus_prefers_more_unique_relation_types() -> None:
    a, b, c, d = _items()
    policy = ConstraintDistributionPolicy()

    less_diverse = [FixedPositionConstraint(a, Position(1)), LeftOfConstraint(a, c), LeftOfConstraint(b, d)]
    more_diverse = [FixedPositionConstraint(a, Position(1)), LeftOfConstraint(a, c), AdjacentConstraint(c, d)]

    assert policy.score(more_diverse) > policy.score(less_diverse)


def test_score_is_deterministic_for_identical_input() -> None:
    a, b, c, d = _items()
    constraints = [
        FixedPositionConstraint(a, Position(1)),
        DirectLeftOfConstraint(a, b),
        RightOfConstraint(d, b),
        AdjacentConstraint(c, d),
    ]
    policy = ConstraintDistributionPolicy()

    assert policy.score(constraints) == policy.score(constraints)
    assert policy.analyze(constraints) == policy.analyze(list(constraints))
