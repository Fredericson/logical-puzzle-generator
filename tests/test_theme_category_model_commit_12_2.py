from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.generator.clue_reducer import ClueReducer
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.metadata import Metadata
from logical_puzzle_generator.themes.presentation import ItemPresentationResolver
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY, ThemeDefinition
from logical_puzzle_generator.themes.tennis import create_template

REQUIRED = {
    "tennis_training": {"training", "backhand_type", "bag_colour", "playing_style", "favourite_surface"},
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


def test_tennis_favourite_surface_is_data_only_with_natural_wording() -> None:
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category = theme.category_by_id("favourite_surface")
    assert category.localized_label("en") == "Favourite Surface"
    assert category.localized_label("de") == "Lieblingsunterlage"
    assert [value.id for value in category.values] == ["clay", "hard_court", "grass", "carpet"]

    instance = theme.create_category_instance(
        category_id="favourite_surface",
        random_source=random.Random(1),
    )
    resolver_en = ItemPresentationResolver(theme, instance, "en")
    resolver_de = ItemPresentationResolver(theme, instance, "de")

    child = Item("Emma")
    clay = Item("clay", category_id="favourite_surface")
    grass = Item("grass", category_id="favourite_surface")
    assert resolver_en.direct_assignment_sentence(child, clay) == "Emma prefers clay."
    assert resolver_de.direct_assignment_sentence(child, clay) == "Emma spielt am liebsten auf Sand."
    assert resolver_en.child_with_theme_phrase(grass) == "the child who prefers grass"
    assert resolver_de.child_with_theme_phrase(grass) == "das Kind, das am liebsten auf Rasen spielt"


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


def test_metadata_keeps_canonical_category_fields_safe() -> None:
    metadata = Metadata(
        title="Title",
        theme="Theme",
        difficulty=1,
        theme_id="tennis_training",
        theme_category_id="bag_colour",
        theme_category_instance_id="bag_colour_1",
        selected_theme_value_ids=("red", "green", "yellow", "blue"),
    )

    assert metadata.thematic_category_id == "bag_colour"
    with pytest.raises(AttributeError):
        metadata.thematic_category_id = "localized label"  # type: ignore[misc]
    assert not hasattr(metadata, "thematic_category_label")


def test_thematic_subset_search_failure_retries_instead_of_using_full_pool(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_thematic_subset(self: PuzzleGenerator, *args: object, **kwargs: object) -> None:
        return None

    monkeypatch.setattr(PuzzleGenerator, "_select_thematic_constraints", no_thematic_subset)

    with pytest.raises(RuntimeError, match="no bounded uniquely solvable thematic clue subset"):
        PuzzleGenerator(
            random_source=random.Random(1),
            difficulty="easy",
            theme="beach_day",
            max_attempts=1,
            clue_reducer=ClueReducer(),
        ).generate(create_template())
