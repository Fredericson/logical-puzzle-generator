from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.engine.assignment_iterator import AssignmentIterator
from logical_puzzle_generator.engine.solver import Solver
from logical_puzzle_generator.generator.difficulty import DifficultyPolicy
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY, ThemeDefinition
from logical_puzzle_generator.themes.tennis import create_template

THEME_IDS = ("tennis_training", "dance_studio", "beach_day", "athletics_training", "zoo_visit")


def test_theme_registry_resolves_all_themes_and_rejects_invalid_ids() -> None:
    assert DEFAULT_THEME_REGISTRY.supported_theme_ids() == THEME_IDS
    for theme_id in THEME_IDS:
        theme = DEFAULT_THEME_REGISTRY.resolve(theme_id)
        assert isinstance(theme, ThemeDefinition)
        assert len(theme.categories) >= 4
        assert len({category.id for category in theme.categories}) == len(theme.categories)
        assert theme.title.en and theme.title.de
        for category in theme.categories:
            assert category.label.en and category.label.de
            if category.is_numeric:
                assert category.values == ()
            else:
                assert len(category.values) >= 4
                assert len({value.id for value in category.values}) == len(category.values)
                assert all(value.label.en and value.label.de for value in category.values)
    with pytest.raises(ValueError, match="Unsupported theme"):
        DEFAULT_THEME_REGISTRY.resolve("space_camp")


def test_theme_definitions_are_immutable() -> None:
    theme = DEFAULT_THEME_REGISTRY.resolve("beach_day")
    with pytest.raises(Exception):
        theme.id = "changed"  # type: ignore[misc]


def test_seeded_random_theme_selection_is_deterministic_and_varied() -> None:
    assert (
        DEFAULT_THEME_REGISTRY.resolve("random", random.Random(12)).id
        == DEFAULT_THEME_REGISTRY.resolve("random", random.Random(12)).id
    )
    assert (
        len(
            {DEFAULT_THEME_REGISTRY.resolve("random", random.Random(seed)).id for seed in range(20)}
        )
        > 1
    )


def test_category_aware_assignment_space_uses_two_four_item_categories() -> None:
    puzzle = PuzzleGenerator(
        random_source=random.Random(3), difficulty="easy", theme="beach_day"
    ).generate(create_template())
    assert len(puzzle.categories) == 2
    assert [len(category.items) for category in puzzle.categories] == [4, 4]
    assert len(list(AssignmentIterator().iterate(puzzle.logical_items))) == 576


def test_generated_theme_puzzle_is_uniquely_solved_across_both_categories() -> None:
    puzzle = PuzzleGenerator(
        random_source=random.Random(5), difficulty="medium", theme="zoo_visit"
    ).generate(create_template())
    result = Solver().solve(puzzle, stop_after=2)
    assert result.has_unique_solution
    assert result.solutions[0] == puzzle.solution.assignment
    theme_items = [item for item in puzzle.logical_items if item.category_id != "children"]
    assert {result.solutions[0].position_of(item).index for item in theme_items} == {1, 2, 3, 4}


@pytest.mark.parametrize(("difficulty", "anchors"), [("easy", 2), ("medium", 1), ("hard", 0)])
def test_difficulty_counts_only_child_fixed_position_anchors(difficulty: str, anchors: int) -> None:
    puzzle = PuzzleGenerator(
        random_source=random.Random(8), difficulty=difficulty, theme="athletics_training"
    ).generate(create_template())
    child_fixed = [
        constraint
        for constraint in puzzle.constraints
        if isinstance(constraint, FixedPositionConstraint)
        and constraint.item.category_id == "children"
    ]
    assert len(child_fixed) == anchors
    assert DifficultyPolicy().fixed_position_count(puzzle) == anchors


def _constraint_signature(puzzle: object) -> tuple[tuple[str, str], ...]:
    return tuple((type(constraint).__name__, constraint.description) for constraint in puzzle.constraints)  # type: ignore[attr-defined]


@pytest.mark.parametrize("theme_id", THEME_IDS)
def test_representative_themed_generation_uses_bounded_varied_clues(theme_id: str) -> None:
    theme = DEFAULT_THEME_REGISTRY.resolve(theme_id)
    category_id = theme.categories[0].id
    generator = PuzzleGenerator(
        random_source=random.Random(41),
        difficulty="easy",
        theme=theme_id,
        category=category_id,
    )
    puzzle = generator.generate(create_template())
    result = Solver().solve(puzzle, stop_after=2)
    assert result.has_unique_solution
    assert result.solutions[0] == puzzle.solution.assignment

    theme_items = [item for item in puzzle.logical_items if item.category_id != "children"]
    thematic_constraints = [
        constraint
        for constraint in puzzle.constraints
        if any(item in theme_items for item in getattr(constraint, "items", ()))
    ]
    if not thematic_constraints:
        thematic_constraints = [
            constraint
            for constraint in puzzle.constraints
            if any(
                getattr(constraint, attr, None) in theme_items
                for attr in ("item", "first", "second", "left", "right")
            )
        ]
    full_pool = generator._derive_thematic_constraints(puzzle.solution, puzzle.items, theme_items)
    assert 0 < len(thematic_constraints) < len(full_pool)
    assert (
        sum(isinstance(constraint, SamePositionConstraint) for constraint in puzzle.constraints) < 4
    )
    assert any(
        isinstance(
            constraint,
            (
                AdjacentConstraint,
                DirectLeftOfConstraint,
                DirectRightOfConstraint,
                LeftOfConstraint,
                RightOfConstraint,
            ),
        )
        for constraint in thematic_constraints
    )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_representative_themed_generation_succeeds_for_all_difficulties(difficulty: str) -> None:
    puzzle = PuzzleGenerator(
        random_source=random.Random(41),
        difficulty=difficulty,
        theme="tennis_training",
        category="training",
    ).generate(create_template())
    assert Solver().solve(puzzle, stop_after=2).has_unique_solution


def test_representative_seed_samples_multiple_categories_and_is_deterministic() -> None:
    families: set[type[object]] = set()
    categories_by_theme: dict[str, set[str]] = {theme_id: set() for theme_id in THEME_IDS}
    for theme_id in THEME_IDS:
        for seed in (1, 2):
            first = PuzzleGenerator(
                random_source=random.Random(seed), difficulty="easy", theme=theme_id
            ).generate(create_template())
            second = PuzzleGenerator(
                random_source=random.Random(seed), difficulty="easy", theme=theme_id
            ).generate(create_template())
            assert first.metadata is not None
            assert second.metadata is not None
            assert first.metadata.theme_category_id == second.metadata.theme_category_id
            assert (
                first.metadata.selected_theme_value_ids == second.metadata.selected_theme_value_ids
            )
            assert _constraint_signature(first) == _constraint_signature(second)
            assert first.solution == second.solution
            categories_by_theme[theme_id].add(first.metadata.theme_category_id)
            for constraint in first.constraints:
                if any(
                    getattr(constraint, attr, None).category_id != "children"
                    for attr in ("item", "first", "second", "left", "right")
                    if getattr(constraint, attr, None) is not None
                ):
                    families.add(type(constraint))

    assert all(len(category_ids) >= 2 for category_ids in categories_by_theme.values())
    assert len(families) > 1
