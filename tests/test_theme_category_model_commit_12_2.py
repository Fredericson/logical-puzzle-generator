from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY, ThemeDefinition
from logical_puzzle_generator.themes.tennis import create_template

REQUIRED = {
    "tennis_training": {"training", "backhand_type", "bag_colour", "playing_style"},
    "dance_studio": {"dance_style", "costume_colour", "dance_move", "music"},
    "beach_day": {"activity", "towel_colour", "drink", "beach_toy"},
    "athletics_training": {"event", "shoe_colour", "training_focus", "equipment"},
    "zoo_visit": {"animal_area", "snack", "souvenir", "meeting_point"},
}


def test_themes_expose_multiple_categories_not_single_category_fields() -> None:
    for theme_id, required_categories in REQUIRED.items():
        theme = DEFAULT_THEME_REGISTRY.resolve(theme_id)
        assert isinstance(theme, ThemeDefinition)
        assert not hasattr(theme, "thematic_category_id")
        assert not hasattr(theme, "category_label")
        assert not hasattr(theme, "values")
        assert not hasattr(theme, "wording")
        category_ids = {category.id for category in theme.categories}
        assert required_categories <= category_ids
        assert len(category_ids) == len(theme.categories)
        for category in theme.categories:
            assert len(category.values) >= 4
            assert len({value.id for value in category.values}) == len(category.values)


def test_tennis_playing_style_has_larger_seeded_value_pool() -> None:
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category = theme.category_by_id("playing_style")
    assert len(category.values) > 4
    first = theme.create_category_instance(category_id="playing_style", random_source=random.Random(10))
    second = theme.create_category_instance(category_id="playing_style", random_source=random.Random(10))
    assert first.selected_value_ids == second.selected_value_ids
    assert len(first.selected_values) == 4
    assert len(set(first.selected_value_ids)) == 4
    assert first.instance_id == "playing_style_1"


def test_omitted_category_is_seeded_and_scoped_to_theme() -> None:
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    first = theme.create_category_instance(category_id=None, random_source=random.Random(4))
    second = theme.create_category_instance(category_id=None, random_source=random.Random(4))
    assert first.category_id == second.category_id
    assert first.selected_value_ids == second.selected_value_ids
    assert len({theme.create_category_instance(category_id=None, random_source=random.Random(seed)).category_id for seed in range(20)}) > 1
    with pytest.raises(ValueError, match="Supported categories"):
        theme.create_category_instance(category_id="activity", random_source=random.Random(1))


def test_generator_stores_selected_category_instance_metadata() -> None:
    puzzle = PuzzleGenerator(
        random_source=random.Random(3),
        difficulty="easy",
        theme="tennis_training",
        category="backhand_type",
    ).generate(create_template())
    assert puzzle.metadata is not None
    assert puzzle.metadata.theme_id == "tennis_training"
    assert puzzle.metadata.theme_category_id == "backhand_type"
    assert puzzle.metadata.theme_category_instance_id == "backhand_type_1"
    assert len(puzzle.metadata.selected_theme_value_ids) == 4
    assert [category.name for category in puzzle.categories] == ["Children", "backhand_type"]
