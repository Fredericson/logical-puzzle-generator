from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
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
    assert DEFAULT_THEME_REGISTRY.resolve("random", random.Random(12)).id == DEFAULT_THEME_REGISTRY.resolve("random", random.Random(12)).id
    assert len({DEFAULT_THEME_REGISTRY.resolve("random", random.Random(seed)).id for seed in range(20)}) > 1


def test_category_aware_assignment_space_uses_two_four_item_categories() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(3), difficulty="easy", theme="beach_day").generate(create_template())
    assert len(puzzle.categories) == 2
    assert [len(category.items) for category in puzzle.categories] == [4, 4]
    assert len(list(AssignmentIterator().iterate(puzzle.logical_items))) == 576


def test_generated_theme_puzzle_is_uniquely_solved_across_both_categories() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(5), difficulty="medium", theme="zoo_visit").generate(create_template())
    result = Solver().solve(puzzle, stop_after=2)
    assert result.has_unique_solution
    assert result.solutions[0] == puzzle.solution.assignment
    theme_items = [item for item in puzzle.logical_items if item.category_id != "children"]
    assert {result.solutions[0].position_of(item).index for item in theme_items} == {1, 2, 3, 4}


@pytest.mark.parametrize(("difficulty", "anchors"), [("easy", 2), ("medium", 1), ("hard", 0)])
def test_difficulty_counts_only_child_fixed_position_anchors(difficulty: str, anchors: int) -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(8), difficulty=difficulty, theme="athletics_training").generate(create_template())
    child_fixed = [constraint for constraint in puzzle.constraints if isinstance(constraint, FixedPositionConstraint) and constraint.item.category_id == "children"]
    assert len(child_fixed) == anchors
    assert DifficultyPolicy().fixed_position_count(puzzle) == anchors
