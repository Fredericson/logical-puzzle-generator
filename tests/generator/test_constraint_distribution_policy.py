from __future__ import annotations

from pathlib import Path

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


def test_policy_source_has_no_difficulty_dependency() -> None:
    source = Path("src/logical_puzzle_generator/generator/constraint_distribution_policy.py").read_text()

    assert "Difficulty" not in source
    assert "DifficultyPolicy" not in source


def test_fixed_position_count_matching_uses_neutral_required_count() -> None:
    a, b, c, d = _items()
    constraints = [
        FixedPositionConstraint(a, Position(1)),
        DirectLeftOfConstraint(a, b),
        AdjacentConstraint(c, d),
    ]
    policy = ConstraintDistributionPolicy()

    assert policy.accepts(constraints, required_fixed_count=1, item_count=4)
    assert not policy.accepts(constraints, required_fixed_count=2, item_count=4)


def test_three_identical_left_of_constraints_are_rejected() -> None:
    a, b, c, d = _items()
    constraints = [LeftOfConstraint(a, b), LeftOfConstraint(a, c), LeftOfConstraint(a, d)]

    assert not ConstraintDistributionPolicy().accepts(constraints, item_count=4)


def test_three_identical_right_of_constraints_are_rejected() -> None:
    a, b, c, d = _items()
    constraints = [RightOfConstraint(b, a), RightOfConstraint(c, a), RightOfConstraint(d, a)]

    assert not ConstraintDistributionPolicy().accepts(constraints, item_count=4)


def test_three_identical_adjacent_constraints_are_rejected() -> None:
    a, b, c, d = _items()
    constraints = [AdjacentConstraint(a, b), AdjacentConstraint(b, c), AdjacentConstraint(c, d)]

    assert not ConstraintDistributionPolicy().accepts(constraints, item_count=4)


def test_two_relation_sets_remain_allowed() -> None:
    a, b, c, _d = _items()
    constraints = [LeftOfConstraint(a, b), LeftOfConstraint(a, c)]

    assert ConstraintDistributionPolicy().accepts(constraints, item_count=4)


def test_varied_relation_set_is_accepted() -> None:
    a, b, c, d = _items()
    constraints = [LeftOfConstraint(a, b), DirectRightOfConstraint(c, b), AdjacentConstraint(c, d)]

    assert ConstraintDistributionPolicy().accepts(constraints, item_count=4)


def test_two_of_one_relation_type_plus_another_type_is_accepted() -> None:
    a, b, c, d = _items()
    constraints = [LeftOfConstraint(a, b), LeftOfConstraint(a, c), AdjacentConstraint(c, d)]

    assert ConstraintDistributionPolicy().accepts(constraints, item_count=4)


def test_relation_set_dominated_by_ordinary_left_right_is_rejected() -> None:
    a, b, c, d = _items()
    constraints = [LeftOfConstraint(a, c), RightOfConstraint(d, b), LeftOfConstraint(b, d)]

    assert not ConstraintDistributionPolicy().accepts(constraints, item_count=4)


def test_score_is_deterministic_for_identical_input() -> None:
    a, b, c, d = _items()
    constraints = [
        FixedPositionConstraint(a, Position(1)),
        DirectLeftOfConstraint(a, b),
        RightOfConstraint(d, b),
        AdjacentConstraint(c, d),
    ]
    policy = ConstraintDistributionPolicy()

    assert policy.score(constraints) == policy.score(list(constraints))
    assert policy.analyze(constraints) == policy.analyze(list(constraints))


def test_varied_accepted_distributions_rank_above_repetitive_accepted_distributions() -> None:
    a, b, c, d = _items()
    policy = ConstraintDistributionPolicy()
    repetitive = [LeftOfConstraint(a, b), LeftOfConstraint(a, c)]
    varied = [LeftOfConstraint(a, b), AdjacentConstraint(c, d)]

    assert policy.accepts(repetitive, item_count=4)
    assert policy.accepts(varied, item_count=4)
    assert policy.score(varied) > policy.score(repetitive)


def test_fixed_position_clues_do_not_improve_relation_diversity_score() -> None:
    a, b, c, d = _items()
    relation_only = [DirectLeftOfConstraint(a, b), AdjacentConstraint(c, d)]
    with_fixed = [FixedPositionConstraint(a, Position(1)), *relation_only]
    policy = ConstraintDistributionPolicy()

    assert policy.score(with_fixed) == policy.score(relation_only)


def test_documentation_does_not_make_distribution_policy_a_difficulty_owner() -> None:
    docs = "\n".join(
        Path(path).read_text()
        for path in [
            "README.md",
            "docs/01_AI_DEVELOPMENT_SPEC.md",
            "docs/02_ARCHITECTURE.md",
            "docs/03_CONTRIBUTING_AI.md",
            "docs/04_ROADMAP.md",
            "docs/05_DECISIONS.md",
            "docs/06_PROMPTS.md",
        ]
    )

    assert "ConstraintDistributionPolicy classifies" not in docs
    assert "ConstraintDistributionPolicy owns difficulty" not in docs
    assert "distribution policy understands Easy" not in docs
