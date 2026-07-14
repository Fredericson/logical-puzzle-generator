import random

import pytest

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.numeric import (
    ExactNumericValueConstraint,
    NumericDifferenceConstraint,
    NumericMultipleConstraint,
)
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.generator.difficulty import (
    Difficulty,
    DifficultyContext,
    DifficultyPolicy,
)
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.solution import Solution
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY, ThemeCategoryInstance


def test_position_context_counts_only_child_fixed_position_assignments() -> None:
    policy = DifficultyPolicy()
    child = Item("Emma")
    other_child = Item("Mia")
    theme_value = Item("blue", category_id="bag_colour")

    constraints = [
        FixedPositionConstraint(child, Position(1)),
        FixedPositionConstraint(theme_value, Position(2)),
        DirectLeftOfConstraint(child, other_child),
        DirectRightOfConstraint(other_child, child),
        LeftOfConstraint(child, other_child),
        RightOfConstraint(other_child, child),
        AdjacentConstraint(child, other_child),
    ]

    assert policy.direct_assignment_count(constraints, context=DifficultyContext.POSITION_PAGE) == 1


def test_fixed_child_theme_context_counts_direct_text_assignments_only() -> None:
    policy = DifficultyPolicy()
    child = Item("Emma")
    blue = Item("blue", category_id="bag_colour")
    red = Item("red", category_id="bag_colour")
    green = Item("green", category_id="bag_colour")

    constraints = [
        SamePositionConstraint(child, blue),
        FixedPositionConstraint(red, Position(3)),
        FixedPositionConstraint(child, Position(1)),
        LeftOfConstraint(blue, red),
        RightOfConstraint(red, blue),
        DirectLeftOfConstraint(blue, green),
        DirectRightOfConstraint(green, red),
        AdjacentConstraint(blue, green),
    ]

    assert (
        policy.direct_assignment_count(
            constraints, context=DifficultyContext.FIXED_CHILD_THEME_PAGE
        )
        == 2
    )


def test_fixed_child_theme_context_counts_direct_numeric_assignments_only() -> None:
    policy = DifficultyPolicy()
    child = Item("Emma")
    other_child = Item("Mia")
    value = Item("racket_count_1_value_4", category_id="racket_count")
    values_by_id = {
        "racket_count_1_value_1": 1,
        "racket_count_1_value_2": 2,
        "racket_count_1_value_4": 4,
        "racket_count_1_value_8": 8,
    }

    constraints = [
        ExactNumericValueConstraint(
            child, 4, category_id="racket_count", values_by_id=values_by_id
        ),
        FixedPositionConstraint(value, Position(2)),
        NumericDifferenceConstraint(
            child, other_child, 2, category_id="racket_count", values_by_id=values_by_id
        ),
        NumericMultipleConstraint(
            child, other_child, 2, category_id="racket_count", values_by_id=values_by_id
        ),
    ]

    assert (
        policy.direct_assignment_count(
            constraints, context=DifficultyContext.FIXED_CHILD_THEME_PAGE
        )
        == 2
    )


def _fixed_positions(children):
    return {child: Position(index) for index, child in enumerate(children, start=1)}


def _solution_for(children, theme_items):
    positions = _fixed_positions(children)
    positions.update({item: Position(index) for index, item in enumerate(theme_items, start=1)})
    return Solution(Assignment(positions))


def test_text_direct_forms_normalize_to_canonical_identities() -> None:
    policy = DifficultyPolicy()
    child = Item("Emma")
    blue = Item("blue", category_id="bag_colour")
    red = Item("red", category_id="bag_colour")
    fixed = {child: Position(2)}
    theme_items = [blue, red]

    same = SamePositionConstraint(child, blue)
    fixed_same = FixedPositionConstraint(blue, Position(2))
    fixed_other_position = FixedPositionConstraint(blue, Position(3))
    fixed_other_value = FixedPositionConstraint(red, Position(2))

    assert (
        policy.theme_direct_assignment_identity(
            same, fixed_child_positions=fixed, theme_items=theme_items
        )
        == policy.theme_direct_assignment_identity(
            fixed_same, fixed_child_positions=fixed, theme_items=theme_items
        )
        == (2, "blue")
    )
    assert policy.theme_direct_assignment_identity(
        fixed_other_position, fixed_child_positions=fixed, theme_items=theme_items
    ) == (3, "blue")
    assert policy.theme_direct_assignment_identity(
        fixed_other_value, fixed_child_positions=fixed, theme_items=theme_items
    ) == (2, "red")


def test_numeric_direct_forms_normalize_to_canonical_identities() -> None:
    policy = DifficultyPolicy()
    child = Item("Emma")
    fixed = {child: Position(2)}
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category = tennis.category_by_id("racket_count")
    instance_id = "racket_count_1"
    selected_values = tuple(
        category.parse_generated_numeric_value_id(
            f"{instance_id}_value_{value}", instance_id=instance_id
        )
        for value in (1, 2, 4, 8)
    )
    instance = ThemeCategoryInstance(category, instance_id, selected_values)
    theme_items = [Item(value.id, category_id="racket_count") for value in selected_values]
    value_item = next(item for item in theme_items if item.name.endswith("_value_4"))
    values_by_id = {value.id: value.numeric_value or 0 for value in selected_values}

    exact = ExactNumericValueConstraint(
        child, 4, category_id="racket_count", values_by_id=values_by_id
    )
    fixed_same = FixedPositionConstraint(value_item, Position(2))

    assert (
        policy.theme_direct_assignment_identity(
            exact,
            fixed_child_positions=fixed,
            theme_items=theme_items,
            category_instance=instance,
        )
        == policy.theme_direct_assignment_identity(
            fixed_same,
            fixed_child_positions=fixed,
            theme_items=theme_items,
            category_instance=instance,
        )
        == (2, value_item.name)
    )


def test_candidate_derivation_creates_text_child_and_position_direct_forms() -> None:
    children = [Item("A"), Item("B"), Item("C"), Item("D")]
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category = tennis.category_by_id("bag_colour")
    instance = ThemeCategoryInstance(category, "bag_colour_1", category.values[:4])
    theme_items = [Item(value.id, category_id=category.id) for value in instance.selected_values]
    generator = PuzzleGenerator(theme="tennis_training", category="bag_colour")
    generator._current_category_instance = instance

    constraints = generator._derive_thematic_constraints(
        _solution_for(children, theme_items), children, theme_items
    )

    assert any(isinstance(constraint, SamePositionConstraint) for constraint in constraints)
    assert any(
        isinstance(constraint, FixedPositionConstraint)
        and constraint.item.category_id == category.id
        for constraint in constraints
    )


def test_candidate_derivation_creates_numeric_child_and_position_direct_forms() -> None:
    children = [Item("A"), Item("B"), Item("C"), Item("D")]
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    instance = tennis.create_category_instance(
        category_id="racket_count", random_source=random.Random(4), instance_index=1
    )
    theme_items = [
        Item(value.id, category_id=instance.category_id) for value in instance.selected_values
    ]
    generator = PuzzleGenerator(theme="tennis_training", category="racket_count")
    generator._current_category_instance = instance

    constraints = generator._derive_thematic_constraints(
        _solution_for(children, theme_items), children, theme_items
    )

    assert any(isinstance(constraint, ExactNumericValueConstraint) for constraint in constraints)
    assert any(
        isinstance(constraint, FixedPositionConstraint)
        and constraint.item.category_id == instance.category_id
        for constraint in constraints
    )


def test_duplicate_direct_anchor_variants_do_not_satisfy_easy_twice() -> None:
    children = [Item("A"), Item("B"), Item("C"), Item("D")]
    values = [Item(f"v{i}", category_id="theme") for i in range(4)]
    generator = PuzzleGenerator(
        theme="tennis_training",
        difficulty="easy",
        fixed_child_positions={child: Position(index + 1) for index, child in enumerate(children)},
    )
    generator._current_theme_items = values
    candidates = [
        SamePositionConstraint(children[0], values[0]),
        FixedPositionConstraint(values[0], Position(1)),
        AdjacentConstraint(values[1], values[2]),
    ]

    assert (
        generator._select_thematic_constraints(
            candidates,
            child_constraints=[],
            children=children,
            theme_items=values,
            solution=_solution_for(children, values),
            difficulty=Difficulty.EASY,
        )
        is None
    )


def _bag_colour_instance(selected_ids=("red", "green", "yellow", "blue")):
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category = tennis.category_by_id("bag_colour")
    values = tuple(category.value_by_id(value_id) for value_id in selected_ids)
    return ThemeCategoryInstance(category, "bag_colour_1", values)


def test_foreign_category_item_with_same_value_id_is_rejected() -> None:
    policy = DifficultyPolicy()
    child = Item("Emma")
    selected = Item("blue", category_id="bag_colour")
    foreign = Item("blue", category_id="racket_colour")

    with pytest.raises(ValueError, match="does not match the selected page item"):
        policy.theme_direct_assignment_identity(
            SamePositionConstraint(child, foreign),
            fixed_child_positions={child: Position(2)},
            theme_items=[selected],
        )


def test_duplicate_selected_theme_item_ids_are_rejected() -> None:
    policy = DifficultyPolicy()
    child = Item("Emma")
    blue = Item("blue", category_id="bag_colour")

    with pytest.raises(ValueError, match="unique IDs"):
        policy.theme_direct_assignment_identity(
            SamePositionConstraint(child, blue),
            fixed_child_positions={child: Position(2)},
            theme_items=[blue, blue],
        )


def test_theme_item_category_must_match_category_instance() -> None:
    policy = DifficultyPolicy()
    child = Item("Emma")
    selected = Item("blue", category_id="racket_colour")

    with pytest.raises(ValueError, match="category does not match"):
        policy.theme_direct_assignment_identity(
            SamePositionConstraint(child, selected),
            fixed_child_positions={child: Position(2)},
            theme_items=[selected],
            category_instance=_bag_colour_instance(),
        )


def test_theme_item_must_belong_to_category_instance_selected_values() -> None:
    policy = DifficultyPolicy()
    child = Item("Emma")
    blue = Item("blue", category_id="bag_colour")

    with pytest.raises(ValueError, match="not part of the category instance"):
        policy.theme_direct_assignment_identity(
            SamePositionConstraint(child, blue),
            fixed_child_positions={child: Position(2)},
            theme_items=[blue],
            category_instance=_bag_colour_instance(("red", "green", "yellow")),
        )


def test_raw_theme_direct_constraint_count_differs_from_canonical_identity_count() -> None:
    policy = DifficultyPolicy()
    child = Item("Emma")
    blue = Item("blue", category_id="bag_colour")
    constraints = [SamePositionConstraint(child, blue), FixedPositionConstraint(blue, Position(2))]

    assert policy.raw_theme_direct_constraint_count(constraints) == 2
    assert (
        len(
            policy.theme_direct_assignment_identities(
                constraints,
                fixed_child_positions={child: Position(2)},
                theme_items=[blue],
            )
        )
        == 1
    )
