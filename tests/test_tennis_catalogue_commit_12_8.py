from __future__ import annotations

import random
from collections import Counter

import pytest

from logical_puzzle_generator.clue_text_renderer import ClueTextRenderer
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
from logical_puzzle_generator.generator.puzzle_book import PuzzleBookGenerator
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.solver import Solver
from logical_puzzle_generator.themes.presentation import ItemPresentationResolver
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY, ThemeCategoryInstance
from logical_puzzle_generator.themes.tennis import create_template

NEW_TENNIS_CATEGORIES = {
    "racket_colour": ("Racket Colour", "Schlägerfarbe"),
    "string_colour": ("String Colour", "Saitenfarbe"),
    "forehand_grip": ("Forehand Grip", "Vorhandgriff"),
    "lucky_charm": ("Lucky Charm", "Glücksbringer"),
    "footwork": ("Footwork", "Schritttechnik"),
    "body_build": ("Player Build", "Spielerstatur"),
    "accessory": ("Accessory", "Accessoire"),
}


def _theme():
    return DEFAULT_THEME_REGISTRY.resolve("tennis_training")


def _resolver(category_id: str, language: str, seed: int = 0):
    theme = _theme()
    category = theme.category_by_id(category_id)
    wanted = globals().get("_WANTED_VALUE_ID")
    selected = list(category.values[:4])
    if wanted is not None and wanted not in {value.id for value in selected}:
        selected[-1] = category.value_by_id(wanted)
    instance = ThemeCategoryInstance(
        category,
        f"{category_id}_1",
        tuple(selected),
    )
    return ItemPresentationResolver(theme, instance, language)


@pytest.mark.parametrize("category_id", sorted(NEW_TENNIS_CATEGORIES))
def test_new_tennis_categories_are_registered_and_create_deterministic_instances(category_id):
    theme = _theme()
    category = theme.category_by_id(category_id)
    en_label, de_label = NEW_TENNIS_CATEGORIES[category_id]

    assert category.id == category_id
    assert category.localized_label("en") == en_label
    assert category.localized_label("de") == de_label
    assert len(category.values) >= 4
    assert len({value.id for value in category.values}) == len(category.values)

    first = theme.create_category_instance(category_id=category_id, random_source=random.Random(42))
    second = theme.create_category_instance(
        category_id=category_id, random_source=random.Random(42)
    )
    repeated = theme.create_category_instance(
        category_id=category_id, random_source=random.Random(42), instance_index=2
    )

    assert first.selected_value_ids == second.selected_value_ids
    assert len(first.selected_values) == 4
    assert len(set(first.selected_value_ids)) == 4
    assert all(value.numeric_value is None for value in first.selected_values)
    assert all(
        Item(value.id, category_id=category_id).category_id == category_id
        for value in first.selected_values
    )
    assert first.instance_id == f"{category_id}_1"
    assert repeated.instance_id == f"{category_id}_2"
    assert repeated.instance_id != first.instance_id


@pytest.mark.parametrize(
    ("category_id", "value_id", "en_direct", "de_direct", "en_position", "de_position"),
    [
        (
            "racket_colour",
            "blue",
            "Emma has a blue racket.",
            "Emma hat einen blauen Schläger.",
            "The blue racket is in Position 3.",
            "Der blaue Schläger befindet sich auf Position 3.",
        ),
        (
            "string_colour",
            "white",
            "Emma plays with white strings.",
            "Emma spielt mit weissen Saiten.",
            "The white strings are in Position 3.",
            "Die weissen Saiten befinden sich auf Position 3.",
        ),
        (
            "forehand_grip",
            "semi_western",
            "Emma uses a Semi-Western forehand grip.",
            "Emma spielt die Vorhand mit einem Semi-Western-Griff.",
            "The Semi-Western forehand grip is in Position 3.",
            "Der Semi-Western-Vorhandgriff befindet sich auf Position 3.",
        ),
        (
            "lucky_charm",
            "lucky_coin",
            "Emma carries a lucky coin as her lucky charm.",
            "Emma hat eine Glücksmünze als Glücksbringer dabei.",
            "The lucky coin is in Position 3.",
            "Die Glücksmünze befindet sich auf Position 3.",
        ),
        (
            "footwork",
            "quick_steps",
            "Emma uses quick steps.",
            "Emma macht schnelle Schritte.",
            "Quick steps belong to Position 3.",
            "Die schnellen Schritte gehören zu Position 3.",
        ),
        (
            "body_build",
            "athletic",
            "Emma has an athletic build.",
            "Emma ist athletisch gebaut.",
            "The athletic child is in Position 3.",
            "Das athletisch gebaute Kind befindet sich auf Position 3.",
        ),
        (
            "accessory",
            "visor",
            "Emma wears a visor.",
            "Emma trägt einen Visor.",
            "The visor is in Position 3.",
            "Der Visor befindet sich auf Position 3.",
        ),
    ],
)
def test_new_tennis_category_direct_and_position_wording(
    category_id, value_id, en_direct, de_direct, en_position, de_position
):
    child = Item("Emma")
    value = Item(value_id, category_id=category_id)
    direct_clue = type("ClueLike", (), {"constraint": SamePositionConstraint(child, value)})()
    position_clue = type(
        "ClueLike", (), {"constraint": FixedPositionConstraint(value, Position(3))}
    )()

    global _WANTED_VALUE_ID
    _WANTED_VALUE_ID = value_id
    try:
        assert (
            ClueTextRenderer("en", presentation_resolver=_resolver(category_id, "en")).render_clue(
                direct_clue
            )
            == en_direct
        )
        assert (
            ClueTextRenderer("de", presentation_resolver=_resolver(category_id, "de")).render_clue(
                direct_clue
            )
            == de_direct
        )
        assert (
            ClueTextRenderer("en", presentation_resolver=_resolver(category_id, "en")).render_clue(
                position_clue
            )
            == en_position
        )
        assert (
            ClueTextRenderer("de", presentation_resolver=_resolver(category_id, "de")).render_clue(
                position_clue
            )
            == de_position
        )
    finally:
        _WANTED_VALUE_ID = None


def test_grammar_sensitive_german_forms_and_swiss_spelling_are_data_driven():
    theme = _theme()
    snippets = []
    for category_id in NEW_TENNIS_CATEGORIES:
        category = theme.category_by_id(category_id)
        for value in category.values:
            snippets.extend(
                [
                    value.display("de"),
                    value.display("de", short=True),
                    value.subject("de"),
                    value.position_subject("de"),
                ]
            )
    text = "\n".join(snippets)

    for expected in [
        "blauen Schläger",
        "roten Schläger",
        "weissen Schläger",
        "weissen Saiten",
        "schwarzen Saiten",
        "Semi-Western-Griff",
        "Kontinentalgriff",
        "Glücksmünze",
        "vierblättriges Kleeblatt",
        "schnelle Schritte",
        "guten Split-Step",
        "gross",
        "schlank",
        "athletisch gebaut",
        "kräftig",
        "einen Visor",
        "eine Sonnenbrille",
        "eine Baseballcap",
        "ein Stirnband",
    ]:
        assert expected in text
    assert "ß" not in text
    assert "Sonnenhut" not in text
    assert "offener Hut" not in text


@pytest.mark.parametrize("category_id", sorted(NEW_TENNIS_CATEGORIES))
def test_new_tennis_categories_support_standalone_generation(category_id):
    puzzle = PuzzleGenerator(
        theme="tennis_training",
        category=category_id,
        random_source=random.Random(12),
        difficulty="easy",
    ).generate(create_template())

    assert puzzle.metadata.theme_category_id == category_id
    assert puzzle.metadata.theme_category_instance_id == f"{category_id}_1"
    assert len(puzzle.metadata.selected_theme_value_ids) == 4
    assert Solver().solve(puzzle).solution_count == 1
    rendered = "\n".join(clue.text for clue in puzzle.clues)
    assert category_id not in rendered
    assert "theme_category_instance_id" not in rendered


def test_puzzle_book_exhausts_all_tennis_categories_before_repetition_and_is_seeded():
    generator = PuzzleBookGenerator(theme="tennis_training", random_source=random.Random(12))
    count = len(generator.available_category_ids)
    selected = generator.select_category_ids(count)
    repeated = PuzzleBookGenerator(
        theme="tennis_training", random_source=random.Random(12)
    ).select_category_ids(count + 1)

    assert count == len(_theme().categories)
    assert set(selected) == set(generator.available_category_ids)
    assert all(amount == 1 for amount in Counter(selected).values())
    assert set(generator.available_category_ids) <= set(repeated)
    assert sorted(Counter(repeated).values()) == [1] * (count - 1) + [2]
    assert selected == PuzzleBookGenerator(
        theme="tennis_training", random_source=random.Random(12)
    ).select_category_ids(count)
    assert set(NEW_TENNIS_CATEGORIES) <= set(selected)
