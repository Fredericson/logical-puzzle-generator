from __future__ import annotations

import random
from collections import Counter
from collections.abc import Iterable, Mapping

import pytest

from logical_puzzle_generator.clue_text_renderer import ClueTextRenderer
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
from logical_puzzle_generator.engine.validator import Validator
from logical_puzzle_generator.generator.difficulty import DifficultyPolicy
from logical_puzzle_generator.generator.puzzle_book import PuzzleBook, PuzzleBookGenerator
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.generator.puzzle_template import PuzzleTemplate
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.metadata import Metadata
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.solver import Solver
from logical_puzzle_generator.themes.presentation import ItemPresentationResolver
from logical_puzzle_generator.themes.registry import (
    DEFAULT_THEME_REGISTRY,
    LocalizedText,
    ThemeCategoryDefinition,
    ThemeCategoryInstance,
    ThemeDefinition,
    ThemeValue,
    _value,
)
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

APPROVED_TENNIS_CATEGORIES = {
    "training",
    "backhand_type",
    "bag_colour",
    "playing_style",
    "favourite_surface",
    "tournament_wins",
    "racket_count",
    "racket_colour",
    "string_colour",
    "forehand_grip",
    "lucky_charm",
    "footwork",
    "body_build",
    "accessory",
}

INTERNAL_FRAGMENTS = (
    "racket_colour",
    "string_colour",
    "forehand_grip",
    "lucky_charm",
    "body_build",
    "baseball_cap",
    "small_teddy",
    "lucky_coin",
    "four_leaf_clover",
    "mini_tennis_ball",
    "short_steps",
    "quick_steps",
    "split_step",
    "theme_category_instance_id",
    "friendship_bracelet",
)

EXPECTED_DIRECT_DE = {
    ("racket_colour", "blue"): "Emma hat einen blauen Schläger.",
    ("racket_colour", "red"): "Emma hat einen roten Schläger.",
    ("racket_colour", "green"): "Emma hat einen grünen Schläger.",
    ("racket_colour", "yellow"): "Emma hat einen gelben Schläger.",
    ("racket_colour", "black"): "Emma hat einen schwarzen Schläger.",
    ("racket_colour", "white"): "Emma hat einen weissen Schläger.",
    ("racket_colour", "pink"): "Emma hat einen pinken Schläger.",
    ("racket_colour", "orange"): "Emma hat einen orangen Schläger.",
    ("string_colour", "white"): "Emma spielt mit weissen Saiten.",
    ("string_colour", "black"): "Emma spielt mit schwarzen Saiten.",
    ("string_colour", "yellow"): "Emma spielt mit gelben Saiten.",
    ("string_colour", "red"): "Emma spielt mit roten Saiten.",
    ("string_colour", "blue"): "Emma spielt mit blauen Saiten.",
    ("string_colour", "green"): "Emma spielt mit grünen Saiten.",
    ("string_colour", "orange"): "Emma spielt mit orangen Saiten.",
    ("string_colour", "pink"): "Emma spielt mit pinken Saiten.",
    ("forehand_grip", "continental"): "Emma spielt die Vorhand mit einem Kontinentalgriff.",
    ("forehand_grip", "eastern"): "Emma spielt die Vorhand mit einem Eastern-Griff.",
    ("forehand_grip", "semi_western"): "Emma spielt die Vorhand mit einem Semi-Western-Griff.",
    ("forehand_grip", "western"): "Emma spielt die Vorhand mit einem Western-Griff.",
    ("lucky_charm", "bracelet"): "Emma hat ein Armband als Glücksbringer dabei.",
    ("lucky_charm", "small_teddy"): "Emma hat einen kleinen Teddybär als Glücksbringer dabei.",
    ("lucky_charm", "keyring"): "Emma hat einen Schlüsselanhänger als Glücksbringer dabei.",
    ("lucky_charm", "lucky_coin"): "Emma hat eine Glücksmünze als Glücksbringer dabei.",
    (
        "lucky_charm",
        "friendship_bracelet",
    ): "Emma hat ein Freundschaftsarmband als Glücksbringer dabei.",
    ("lucky_charm", "mini_tennis_ball"): "Emma hat einen Mini-Tennisball als Glücksbringer dabei.",
    (
        "lucky_charm",
        "four_leaf_clover",
    ): "Emma hat ein vierblättriges Kleeblatt als Glücksbringer dabei.",
    ("lucky_charm", "mascot"): "Emma hat ein Maskottchen als Glücksbringer dabei.",
    ("footwork", "short_steps"): "Emma macht kurze Schritte.",
    ("footwork", "long_steps"): "Emma macht lange Schritte.",
    ("footwork", "quick_steps"): "Emma macht schnelle Schritte.",
    ("footwork", "split_step"): "Emma hat einen guten Split-Step.",
    ("body_build", "tall"): "Emma ist gross.",
    ("body_build", "medium_height"): "Emma ist mittelgross.",
    ("body_build", "small"): "Emma ist klein.",
    ("body_build", "slim"): "Emma ist schlank.",
    ("body_build", "athletic"): "Emma ist athletisch gebaut.",
    ("body_build", "strong"): "Emma ist kräftig.",
    ("accessory", "baseball_cap"): "Emma trägt eine Baseballcap.",
    ("accessory", "visor"): "Emma trägt einen Visor.",
    ("accessory", "sunglasses"): "Emma trägt eine Sonnenbrille.",
    ("accessory", "headband"): "Emma trägt ein Stirnband.",
}

EXPECTED_DATIVE_DE = {
    ("racket_colour", "blue"): "dem blauen Schläger",
    ("racket_colour", "red"): "dem roten Schläger",
    ("racket_colour", "green"): "dem grünen Schläger",
    ("racket_colour", "yellow"): "dem gelben Schläger",
    ("racket_colour", "black"): "dem schwarzen Schläger",
    ("racket_colour", "white"): "dem weissen Schläger",
    ("racket_colour", "pink"): "dem pinken Schläger",
    ("racket_colour", "orange"): "dem orangen Schläger",
    ("string_colour", "white"): "den weissen Saiten",
    ("string_colour", "black"): "den schwarzen Saiten",
    ("string_colour", "green"): "den grünen Saiten",
    ("forehand_grip", "continental"): "dem Kontinentalgriff",
    ("forehand_grip", "eastern"): "dem Eastern-Vorhandgriff",
    ("forehand_grip", "semi_western"): "dem Semi-Western-Vorhandgriff",
    ("forehand_grip", "western"): "dem Western-Vorhandgriff",
    ("accessory", "baseball_cap"): "der Baseballcap",
    ("accessory", "visor"): "dem Visor",
    ("accessory", "sunglasses"): "der Sonnenbrille",
    ("accessory", "headband"): "dem Stirnband",
    ("lucky_charm", "four_leaf_clover"): "dem vierblättrigen Kleeblatt",
    ("footwork", "split_step"): "dem guten Split-Step",
    ("body_build", "athletic"): "dem athletisch gebauten Kind",
    ("lucky_charm", "small_teddy"): "dem kleinen Teddybär",
    ("body_build", "medium_height"): "dem mittelgrossen Kind",
    ("lucky_charm", "friendship_bracelet"): "dem Freundschaftsarmband",
}

EXPECTED_POSITION_DE = {
    (
        "lucky_charm",
        "friendship_bracelet",
    ): "Das Freundschaftsarmband befindet sich auf Position 3.",
    ("string_colour", "white"): "Die weissen Saiten befinden sich auf Position 3.",
    ("footwork", "quick_steps"): "Die schnellen Schritte gehören zu Position 3.",
    ("footwork", "split_step"): "Der gute Split-Step befindet sich auf Position 3.",
    ("accessory", "baseball_cap"): "Die Baseballcap befindet sich auf Position 3.",
    ("accessory", "visor"): "Der Visor befindet sich auf Position 3.",
    ("accessory", "sunglasses"): "Die Sonnenbrille befindet sich auf Position 3.",
    ("accessory", "headband"): "Das Stirnband befindet sich auf Position 3.",
}

EXPECTED_POSITION_EN = {
    ("accessory", "sunglasses"): "The sunglasses are in Position 3.",
    ("lucky_charm", "friendship_bracelet"): "The friendship bracelet is in Position 3.",
}


def _theme() -> ThemeDefinition:
    return DEFAULT_THEME_REGISTRY.resolve("tennis_training")


def _category(category_id: str) -> ThemeCategoryDefinition:
    return _theme().category_by_id(category_id)


def new_category_value_cases() -> list[tuple[str, str]]:
    return [
        (category_id, value.id)
        for category_id in sorted(NEW_TENNIS_CATEGORIES)
        for value in _category(category_id).values
    ]


def category_instance_with_required_values(
    category_id: str,
    required_value_ids: tuple[str, ...],
    *,
    instance_index: int = 1,
) -> ThemeCategoryInstance:
    category = _category(category_id)
    selected: list[ThemeValue] = []
    for requested_id in required_value_ids:
        if requested_id not in {value.id for value in selected}:
            selected.append(category.value_by_id(requested_id))
    selected.extend(
        value for value in category.values if value.id not in {item.id for item in selected}
    )
    return ThemeCategoryInstance(category, f"{category_id}_{instance_index}", tuple(selected[:4]))


def category_instance_for_value(
    category_id: str, value_id: str, *extra_value_ids: str
) -> ThemeCategoryInstance:
    return category_instance_with_required_values(category_id, (value_id, *extra_value_ids))


def resolver_for_value(
    category_id: str, value_id: str, language: str, *extra_value_ids: str
) -> ItemPresentationResolver:
    return ItemPresentationResolver(
        _theme(), category_instance_for_value(category_id, value_id, *extra_value_ids), language
    )


def clue_for(constraint: Constraint) -> Clue:
    clue_types = {
        FixedPositionConstraint: ClueType.FIXED_POSITION,
        SamePositionConstraint: ClueType.SAME_POSITION,
        LeftOfConstraint: ClueType.LEFT_OF,
        AdjacentConstraint: ClueType.ADJACENT,
    }
    for constraint_type, clue_type in clue_types.items():
        if isinstance(constraint, constraint_type):
            return Clue(clue_type, "", constraint)
    raise AssertionError(f"No test clue type mapping for {type(constraint).__name__}.")


@pytest.mark.parametrize(
    ("constraint", "expected_clue_type"),
    [
        (FixedPositionConstraint(Item("Emma"), Position(1)), ClueType.FIXED_POSITION),
        (
            SamePositionConstraint(Item("Emma"), Item("blue", "racket_colour")),
            ClueType.SAME_POSITION,
        ),
        (
            LeftOfConstraint(Item("blue", "racket_colour"), Item("red", "racket_colour")),
            ClueType.LEFT_OF,
        ),
        (
            AdjacentConstraint(Item("blue", "racket_colour"), Item("red", "racket_colour")),
            ClueType.ADJACENT,
        ),
    ],
)
def test_clue_for_uses_matching_clue_type(constraint, expected_clue_type) -> None:
    assert clue_for(constraint).clue_type is expected_clue_type


def render_direct(category_id: str, value_id: str, language: str) -> str:
    clue = clue_for(SamePositionConstraint(Item("Emma"), Item(value_id, category_id)))
    return ClueTextRenderer(
        language, presentation_resolver=resolver_for_value(category_id, value_id, language)
    ).render_clue(clue)


def render_position(category_id: str, value_id: str, language: str) -> str:
    clue = clue_for(FixedPositionConstraint(Item(value_id, category_id), Position(3)))
    return ClueTextRenderer(
        language, presentation_resolver=resolver_for_value(category_id, value_id, language)
    ).render_clue(clue)


def assert_child_facing(text: str, *, category_id: str, value_id: str) -> None:
    assert text
    assert text.endswith(".")
    assert "{" not in text and "}" not in text
    assert category_id not in text
    if "_" in value_id:
        assert value_id not in text
    assert "theme_category_instance_id" not in text


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


def test_exact_approved_tennis_catalogue_is_preserved() -> None:
    assert {category.id for category in _theme().categories} == APPROVED_TENNIS_CATEGORIES


@pytest.mark.parametrize("theme_id", DEFAULT_THEME_REGISTRY.supported_theme_ids())
def test_every_registered_theme_has_complete_localized_presentation(theme_id: str) -> None:
    theme = DEFAULT_THEME_REGISTRY.resolve(theme_id)
    assert theme.id
    assert theme.localized_title("en")
    assert theme.localized_title("de")
    assert theme.categories
    category_ids = [category.id for category in theme.categories]
    assert len(set(category_ids)) == len(category_ids)
    for category in theme.categories:
        assert category.id
        assert category.localized_label("en")
        assert category.localized_label("de")
        if category.is_numeric:
            assert category.numeric_minimum >= 0
            assert category.numeric_maximum > category.numeric_minimum
            assert category.numeric_maximum - category.numeric_minimum + 1 >= 4
            assert category.wording.numeric_exact is not None
            assert category.wording.numeric_position_exact is not None
            continue
        assert len(category.values) >= 4
        value_ids = [value.id for value in category.values]
        assert len(set(value_ids)) == len(value_ids)
        for value in category.values:
            assert value.id
            visible = (
                value.display("en"),
                value.display("de"),
                value.display("en", short=True),
                value.display("de", short=True),
                value.subject("en"),
                value.subject("de"),
                value.dative_subject("en"),
                value.dative_subject("de"),
                value.position_subject("en"),
                value.position_subject("de"),
            )
            assert all(text.strip() for text in visible)
            if value.position_anchor_sentence is not None:
                assert value.position_anchor("en", 3)
                assert value.position_anchor("de", 3)
                assert "{position}" in value.position_anchor_sentence.en
                assert "{position}" in value.position_anchor_sentence.de
            assert (value.dative_subject_phrase is None) or (
                value.dative_subject_phrase.en and value.dative_subject_phrase.de
            )
            assert (value.position_subject_phrase is None) or (
                value.position_subject_phrase.en and value.position_subject_phrase.de
            )
            assert "ß" not in "\n".join(visible)


@pytest.mark.parametrize(("category_id", "value_id"), new_category_value_cases())
def test_every_new_tennis_value_has_complete_child_facing_presentation(category_id, value_id):
    category = _category(category_id)
    value = category.value_by_id(value_id)
    all_ids = [candidate.id for candidate in category.values]

    assert value.id
    assert all_ids.count(value.id) == 1
    visible = [
        value.label.en,
        value.label.de,
        value.display("en", short=True),
        value.display("de", short=True),
        value.subject("en"),
        value.subject("de"),
        value.position_subject("en"),
        value.position_subject("de"),
    ]
    if value.position_anchor_sentence is not None:
        visible.extend(
            [
                value.position_anchor("en", 3) or "",
                value.position_anchor("de", 3) or "",
            ]
        )
    for text in visible:
        assert text.strip()
        assert "{" not in text and "}" not in text
        assert category_id not in text
        if "_" in value_id:
            assert value_id not in text
    assert "ß" not in "\n".join(text for text in visible if text)


@pytest.mark.parametrize(("category_id", "value_id"), new_category_value_cases())
def test_every_new_tennis_value_renders_direct_and_position_clues(category_id, value_id):
    direct_en = render_direct(category_id, value_id, "en")
    direct_de = render_direct(category_id, value_id, "de")
    position_en = render_position(category_id, value_id, "en")
    position_de = render_position(category_id, value_id, "de")

    for rendered in (direct_en, direct_de, position_en, position_de):
        assert_child_facing(rendered, category_id=category_id, value_id=value_id)
    assert "ß" not in direct_de + position_de


@pytest.mark.parametrize(
    ("category_id", "value_id", "expected_direct_de"),
    [
        (category_id, value_id, expected)
        for (category_id, value_id), expected in EXPECTED_DIRECT_DE.items()
    ],
)
def test_grammar_sensitive_direct_german_sentences(category_id, value_id, expected_direct_de):
    assert render_direct(category_id, value_id, "de") == expected_direct_de


@pytest.mark.parametrize(
    ("category_id", "value_id", "expected_fragment"),
    [
        (category_id, value_id, expected)
        for (category_id, value_id), expected in EXPECTED_DATIVE_DE.items()
    ],
)
def test_grammar_sensitive_dative_forms_appear_in_relative_clues(
    category_id, value_id, expected_fragment
):
    category = _category(category_id)
    other = next(value for value in category.values if value.id != value_id)
    clue = clue_for(AdjacentConstraint(Item(other.id, category_id), Item(value_id, category_id)))
    rendered = ClueTextRenderer(
        "de", presentation_resolver=resolver_for_value(category_id, value_id, "de")
    ).render_clue(clue)

    assert expected_fragment in rendered
    assert_child_facing(rendered, category_id=category_id, value_id=value_id)
    assert other.id not in rendered
    assert "ß" not in rendered


@pytest.mark.parametrize(
    ("category_id", "value_id", "expected_position_de"),
    [
        (category_id, value_id, expected)
        for (category_id, value_id), expected in EXPECTED_POSITION_DE.items()
    ],
)
def test_grammar_sensitive_position_german_sentences(category_id, value_id, expected_position_de):
    assert render_position(category_id, value_id, "de") == expected_position_de


@pytest.mark.parametrize(
    ("category_id", "value_id", "expected_position_en"),
    [
        (category_id, value_id, expected)
        for (category_id, value_id), expected in EXPECTED_POSITION_EN.items()
    ],
)
def test_grammar_sensitive_position_english_sentences(category_id, value_id, expected_position_en):
    assert render_position(category_id, value_id, "en") == expected_position_en


@pytest.mark.parametrize("category_id", sorted(NEW_TENNIS_CATEGORIES))
def test_relative_clues_render_every_value_as_first_and_second_item(category_id):
    values = _category(category_id).values
    for first, second in zip(values, values[1:] + values[:1]):
        for constraint in (
            LeftOfConstraint(Item(first.id, category_id), Item(second.id, category_id)),
            AdjacentConstraint(Item(second.id, category_id), Item(first.id, category_id)),
        ):
            clue = clue_for(constraint)
            rendered_en = ClueTextRenderer(
                "en",
                presentation_resolver=resolver_for_value(category_id, first.id, "en", second.id),
            ).render_clue(clue)
            rendered_de = ClueTextRenderer(
                "de",
                presentation_resolver=resolver_for_value(category_id, first.id, "de", second.id),
            ).render_clue(clue)
            assert_child_facing(rendered_en, category_id=category_id, value_id=first.id)
            assert_child_facing(rendered_de, category_id=category_id, value_id=first.id)
            if "_" in second.id:
                assert second.id not in rendered_en + rendered_de
            assert "ß" not in rendered_de


def test_lucky_charm_replaces_hair_ribbon_with_friendship_bracelet() -> None:
    lucky_charm = _category("lucky_charm")
    value_ids = [value.id for value in lucky_charm.values]

    assert "hair_ribbon" not in value_ids
    assert "friendship_bracelet" in value_ids
    friendship_bracelet = lucky_charm.value_by_id("friendship_bracelet")
    assert friendship_bracelet.display("en", short=True) == "Friendship Bracelet"
    assert friendship_bracelet.display("de", short=True) == "Freundschaftsarmband"
    assert friendship_bracelet.dative_subject("de") == "dem Freundschaftsarmband"


def test_accessory_values_are_exactly_the_approved_tennis_values() -> None:
    accessory = _category("accessory")

    assert [value.id for value in accessory.values] == [
        "baseball_cap",
        "visor",
        "sunglasses",
        "headband",
    ]
    assert [value.display("en", short=True) for value in accessory.values] == [
        "Baseball Cap",
        "Visor",
        "Sunglasses",
        "Headband",
    ]
    assert [value.display("de", short=True) for value in accessory.values] == [
        "Baseballcap",
        "Visor",
        "Sonnenbrille",
        "Stirnband",
    ]
    visible = "\n".join(
        presentation
        for value in accessory.values
        for presentation in (value.display("en"), value.display("de"), value.subject("de"))
    )
    assert "sun_hat" not in visible
    assert "open_hat" not in visible
    assert "Sonnenhut" not in visible
    assert "offener Hut" not in visible


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"dative_subject_en": "the value"}, "Dative subject"),
        ({"dative_subject_de": "dem Wert"}, "Dative subject"),
        ({"position_subject_en": "The value"}, "Position subject"),
        ({"position_subject_de": "Der Wert"}, "Position subject"),
        ({"position_anchor_en": "The value is in Position {position}."}, "Position-anchor"),
        ({"position_anchor_de": "Der Wert ist auf Position {position}."}, "Position-anchor"),
    ],
)
def test_optional_localized_presentation_pairs_reject_missing_language(kwargs, message) -> None:
    with pytest.raises(ValueError, match=message):
        _value("half_pair", "value", "Wert", **kwargs)


def test_position_anchor_sentence_rejects_unknown_or_missing_placeholders() -> None:
    with pytest.raises(ValueError, match="unsupported placeholder"):
        ThemeValue(
            "bad_anchor",
            LocalizedText("value", "Wert"),
            position_anchor_sentence=LocalizedText(
                "The value is at {slot}.", "Der Wert ist bei {slot}."
            ),
        )
    with pytest.raises(ValueError, match="must include"):
        ThemeValue(
            "missing_anchor",
            LocalizedText("value", "Wert"),
            position_anchor_sentence=LocalizedText("The value is here.", "Der Wert ist hier."),
        )
    with pytest.raises(ValueError, match="both English and German"):
        _value("half_anchor", "value", "Wert", position_anchor_en="At Position {position}.")


@pytest.mark.parametrize("category_id", sorted(NEW_TENNIS_CATEGORIES))
@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_new_tennis_categories_support_standalone_generation(category_id, difficulty):
    difficulty_policy = DifficultyPolicy()
    expected_difficulty = difficulty_policy.normalize(difficulty)
    assert expected_difficulty is not None
    expected_child_position_anchors = {"easy": 2, "medium": 1, "hard": 0}
    puzzle = PuzzleGenerator(
        theme="tennis_training",
        category=category_id,
        random_source=random.Random(12),
        difficulty=difficulty,
    ).generate(create_template())

    assert puzzle.metadata.theme_id == "tennis_training"
    assert puzzle.metadata.theme_category_id == category_id
    assert puzzle.metadata.theme_category_instance_id == f"{category_id}_1"
    assert puzzle.metadata.difficulty == expected_difficulty.metadata_value
    assert len(puzzle.metadata.selected_theme_value_ids) == 4
    assert len(set(puzzle.metadata.selected_theme_value_ids)) == 4
    assert len(puzzle.clues) == len(puzzle.constraints)
    result = Solver().solve(puzzle)
    assert result.statistics.assignments_checked >= 24 * 24
    assert result.solution_count == 1
    child_position_anchors = [
        constraint
        for constraint in puzzle.constraints
        if isinstance(constraint, FixedPositionConstraint)
        and constraint.item.category_id == CHILDREN_CATEGORY_ID
    ]
    assert len(child_position_anchors) == expected_child_position_anchors[difficulty]
    theme = _theme()
    category_instance = category_instance_from_puzzle_metadata(theme, puzzle)
    resolver = ItemPresentationResolver(theme, category_instance, "de")
    rendered = "\n".join(
        ClueTextRenderer("de", presentation_resolver=resolver).render_clue(clue)
        for clue in puzzle.clues
    )
    assert category_id not in rendered
    assert puzzle.metadata.theme_category_instance_id not in rendered
    assert "theme_category_instance_id" not in rendered
    for value_id in puzzle.metadata.selected_theme_value_ids:
        if "_" in value_id:
            assert value_id not in rendered
    assert "ß" not in rendered


def category_instance_from_puzzle_metadata(
    theme: ThemeDefinition, puzzle: Puzzle
) -> ThemeCategoryInstance:
    metadata = puzzle.metadata
    if (
        metadata is None
        or not metadata.theme_category_id
        or not metadata.theme_category_instance_id
        or not metadata.selected_theme_value_ids
    ):
        raise ValueError("The puzzle does not contain complete Theme category metadata.")
    category = theme.category_by_id(metadata.theme_category_id)
    if category.is_numeric:
        selected = tuple(
            category.parse_generated_numeric_value_id(
                value_id, instance_id=metadata.theme_category_instance_id
            )
            for value_id in metadata.selected_theme_value_ids
        )
    else:
        selected = tuple(
            category.value_by_id(value_id) for value_id in metadata.selected_theme_value_ids
        )
    return ThemeCategoryInstance(category, metadata.theme_category_instance_id, selected)


def _theme_items(page: Puzzle) -> list[Item]:
    return [item for item in page.logical_items if item.category_id != CHILDREN_CATEGORY_ID]


def test_category_instance_reconstruction_requires_theme_metadata() -> None:
    puzzle = Puzzle(
        items=[],
        constraints=[],
        clues=[],
        categories=[],
        metadata=Metadata(
            title="Incomplete", theme="Tennis", difficulty=1, selected_theme_value_ids=("blue",)
        ),
    )

    with pytest.raises(
        ValueError, match="The puzzle does not contain complete Theme category metadata"
    ):
        category_instance_from_puzzle_metadata(_theme(), puzzle)


def _theme_direct_count(page: Puzzle, book: PuzzleBook) -> int:
    return len(
        DifficultyPolicy().theme_direct_assignment_identities(
            page.constraints,
            fixed_child_positions=page.fixed_positions,
            theme_items=_theme_items(page),
            category_instance=category_instance_from_puzzle_metadata(book.theme, page),
        )
    )


@pytest.mark.parametrize("category_id", sorted(NEW_TENNIS_CATEGORIES))
@pytest.mark.parametrize(("difficulty", "direct_count"), [("easy", 2), ("medium", 1), ("hard", 0)])
def test_new_tennis_categories_support_fixed_child_puzzle_book_pages(
    category_id, difficulty, direct_count
):
    class OneCategory(PuzzleBookGenerator):
        def select_category_ids(self, theme_page_count: int) -> tuple[str, ...]:
            return (category_id,)

    book = OneCategory(
        theme="tennis_training", random_source=random.Random(91), difficulty=difficulty
    ).generate(theme_page_count=1)
    page = book.theme_puzzles[0]

    assert len(page.constraints) == len(page.clues) == 3
    assert _theme_direct_count(page, book) == direct_count
    assert page.fixed_positions == dict(book.position_puzzle.solution.assignment.positions)
    assert all(
        not (
            isinstance(constraint, FixedPositionConstraint)
            and constraint.item.category_id == CHILDREN_CATEGORY_ID
        )
        for constraint in page.constraints
    )
    assert Validator().has_unique_solution(page)
    for child, position in page.fixed_positions.items():
        assert page.solution.assignment.position_of(child) == position


def test_puzzle_book_exhausts_all_tennis_categories_before_repetition_and_is_seeded():
    generator = PuzzleBookGenerator(theme="tennis_training", random_source=random.Random(12))
    registered_count = len(_theme().categories)
    selected = generator.select_category_ids(registered_count)
    repeated_once = PuzzleBookGenerator(
        theme="tennis_training", random_source=random.Random(12)
    ).select_category_ids(registered_count + 1)
    repeated_more = PuzzleBookGenerator(
        theme="tennis_training", random_source=random.Random(12)
    ).select_category_ids(registered_count + 3)

    assert registered_count == len(generator.available_category_ids)
    assert set(selected) == set(generator.available_category_ids)
    assert all(amount == 1 for amount in Counter(selected).values())
    assert set(generator.available_category_ids) <= set(repeated_once)
    assert sorted(Counter(repeated_once).values()) == [1] * (registered_count - 1) + [2]
    assert set(generator.available_category_ids) <= set(repeated_more)
    assert sum(amount - 1 for amount in Counter(repeated_more).values()) == 3
    assert selected == PuzzleBookGenerator(
        theme="tennis_training", random_source=random.Random(12)
    ).select_category_ids(registered_count)
    assert set(NEW_TENNIS_CATEGORIES) <= set(selected)


def _pdf_text_bytes(path) -> str:
    return path.read_bytes().decode("latin-1", errors="ignore")


def _pdf_page_count(path) -> int:
    text = _pdf_text_bytes(path)
    return text.count("/Type /Page") - text.count("/Type /Pages")


def _controlled_theme_page(
    category_instance: ThemeCategoryInstance,
    fixed_child_positions: Mapping[Item, Position],
) -> Puzzle:
    class ControlledPuzzleGenerator(PuzzleGenerator):
        def _select_category_instance(
            self, source: PuzzleTemplate | Puzzle | Iterable[Item]
        ) -> ThemeCategoryInstance | None:
            if self._category_id != category_instance.category_id:
                raise ValueError(
                    "Controlled category instance does not match the generator category."
                )
            return category_instance

    return ControlledPuzzleGenerator(
        theme="tennis_training",
        category=category_instance.category_id,
        random_source=random.Random(77),
        difficulty="easy",
        fixed_child_positions=dict(fixed_child_positions),
    ).generate(tuple(fixed_child_positions))


def test_controlled_long_german_values_and_pdf_pages_remain_one_page_each(tmp_path):
    position_puzzle = PuzzleGenerator(random_source=random.Random(42), difficulty="easy").generate(
        create_template()
    )
    assert position_puzzle.solution is not None
    fixed_child_positions = dict(position_puzzle.solution.assignment.positions)
    controlled_instances = (
        category_instance_with_required_values("lucky_charm", ("four_leaf_clover",)),
        category_instance_with_required_values("forehand_grip", ("semi_western",)),
        category_instance_with_required_values("body_build", ("athletic",)),
    )
    theme_pages = tuple(
        _controlled_theme_page(instance, fixed_child_positions) for instance in controlled_instances
    )
    book = PuzzleBook(_theme(), tuple(fixed_child_positions), position_puzzle, theme_pages)
    pages_by_category = {page.metadata.theme_category_id: page for page in book.theme_puzzles}

    assert "four_leaf_clover" in pages_by_category["lucky_charm"].metadata.selected_theme_value_ids
    assert "semi_western" in pages_by_category["forehand_grip"].metadata.selected_theme_value_ids
    assert "athletic" in pages_by_category["body_build"].metadata.selected_theme_value_ids
    assert controlled_instances[0].value_by_id("four_leaf_clover").display("de", short=True) == (
        "Vierblättriges Kleeblatt"
    )
    assert controlled_instances[1].value_by_id("semi_western").display("de", short=True) == (
        "Semi-Western"
    )
    assert controlled_instances[2].value_by_id("athletic").display("de", short=True) == (
        "Athletisch"
    )
    for instance in controlled_instances:
        assert len(instance.selected_values) == 4
        assert len(set(instance.selected_value_ids)) == 4

    for page in book.theme_puzzles:
        assert len(page.constraints) == len(page.clues) == 3
        assert _theme_direct_count(page, book) == 2
        assert page.fixed_positions == fixed_child_positions
        assert all(
            not (
                isinstance(constraint, FixedPositionConstraint)
                and constraint.item.category_id == CHILDREN_CATEGORY_ID
            )
            for constraint in page.constraints
        )
        result = Solver().solve(page)
        assert result.solution_count == 1
        assert page.solution is not None
        assert result.solutions[0].positions == page.solution.assignment.positions

    puzzle_path = tmp_path / "controlled-tennis-book.pdf"
    solution_path = tmp_path / "controlled-tennis-book-solution.pdf"
    PdfGenerator(language="de").create_puzzle_book_pdf(book, puzzle_path)
    PdfGenerator(language="de").create_puzzle_book_solution_pdf(book, solution_path)

    assert _pdf_page_count(puzzle_path) == 5
    assert _pdf_page_count(solution_path) == 1
    puzzle_text = _pdf_text_bytes(puzzle_path)
    solution_text = _pdf_text_bytes(solution_path)
    assert "Seite 1 / 5" in puzzle_text
    assert "Seite 5 / 5" in puzzle_text
    assert "Seite 1 / 1" in solution_text

    rendered_clues = []
    for page in book.theme_puzzles:
        resolver = ItemPresentationResolver(
            book.theme, category_instance_from_puzzle_metadata(book.theme, page), "de"
        )
        rendered_clues.extend(
            ClueTextRenderer("de", presentation_resolver=resolver).render_clue(clue)
            for clue in page.clues
        )
    rendered_text = "\n".join(rendered_clues)
    for forbidden in INTERNAL_FRAGMENTS:
        assert forbidden not in rendered_text
    assert "Sonnenhut" not in rendered_text
    assert "offener Hut" not in rendered_text
    assert "ß" not in rendered_text
