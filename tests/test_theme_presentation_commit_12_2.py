from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.clue_text_renderer import ClueTextRenderer
from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.localization import Language
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.themes.presentation import ItemPresentationResolver
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY
from logical_puzzle_generator.themes.tennis import create_template


def _resolver(theme_id: str, category_id: str, language: str):
    theme = DEFAULT_THEME_REGISTRY.resolve(theme_id)
    instance = theme.create_category_instance(
        category_id=category_id, random_source=random.Random(0)
    )
    return ItemPresentationResolver(theme, instance, language)


LANGUAGE_FORMS = (Language.ENGLISH, Language.GERMAN, "en", "de", "english", "german", "deutsch")
INTERNAL_IDS = (
    "sand_castle",
    "deck_chair",
    "shot_put",
    "pole_vault",
    "water_pistol",
    "cha_cha_cha",
)


@pytest.mark.parametrize("language", LANGUAGE_FORMS)
def test_theme_localization_uses_central_language_parser(language) -> None:
    beach = DEFAULT_THEME_REGISTRY.resolve("beach_day")
    title = beach.localized_title(language)
    if language in (Language.GERMAN, "de", "german", "deutsch"):
        assert title == "Strandtag"
    else:
        assert title == "Beach Day"


def test_presentation_resolver_rejects_unknown_theme_value() -> None:
    resolver = _resolver("beach_day", "activity", "de")
    assert resolver.item_label(Item("Mia")) == "Mia"
    assert (
        resolver.short_theme_label(Item("water_pistol", category_id="activity")) == "Wasserpistole"
    )
    with pytest.raises(ValueError, match="no thematic value"):
        resolver.short_theme_label(Item("deck_chair_typo", category_id="activity"))


@pytest.mark.parametrize(
    ("theme_id", "category_id", "value_id", "de_expected", "en_expected"),
    [
        (
            "tennis_training",
            "training",
            "forehand",
            "Mia trainiert die Vorhand.",
            "Mia practises the forehand.",
        ),
        ("dance_studio", "dance_style", "salsa", "Mia tanzt Salsa.", "Mia dances salsa."),
        ("beach_day", "activity", "shells", "Mia sucht Muscheln.", "Mia collects shells."),
        (
            "athletics_training",
            "event",
            "pole_vault",
            "Mia übt Stabhochsprung.",
            "Mia practises pole vault.",
        ),
        (
            "zoo_visit",
            "animal_area",
            "crocodiles",
            "Mia besucht die Krokodile.",
            "Mia visits the crocodiles.",
        ),
    ],
)
def test_direct_assignment_clues_are_theme_specific_and_natural(
    theme_id, category_id, value_id, de_expected, en_expected
) -> None:
    child = Item("Mia")
    theme_item = Item(value_id, category_id=category_id)
    constraint = SamePositionConstraint(child, theme_item)
    clue = type("ClueLike", (), {"constraint": constraint})()

    de_resolver = _resolver(theme_id, category_id, "de")
    en_resolver = _resolver(theme_id, category_id, "en")

    assert (
        ClueTextRenderer("de", presentation_resolver=de_resolver).render_clue(clue) == de_expected
    )
    assert (
        ClueTextRenderer("en", presentation_resolver=en_resolver).render_clue(clue) == en_expected
    )


@pytest.mark.parametrize("constraint_factory", [LeftOfConstraint, AdjacentConstraint])
def test_theme_relation_clues_do_not_render_theme_values_as_children(constraint_factory) -> None:
    resolver = _resolver("beach_day", "activity", "de")
    child = Item("Lara")
    shells = Item("shells", category_id="activity")
    clue = type("ClueLike", (), {"constraint": constraint_factory(child, shells)})()
    rendered = ClueTextRenderer("de", presentation_resolver=resolver).render_clue(clue)

    assert "Kind" in rendered
    assert "dem Kind, das Muscheln sucht" in rendered
    assert "shells" not in rendered


def test_thematic_fixed_position_clue_uses_child_with_theme_phrase() -> None:
    resolver = _resolver("zoo_visit", "animal_area", "de")
    clue = type(
        "ClueLike",
        (),
        {
            "constraint": FixedPositionConstraint(
                Item("crocodiles", category_id="animal_area"), Position(2)
            )
        },
    )()

    assert (
        ClueTextRenderer("de", presentation_resolver=resolver).render_clue(clue)
        == "das Kind bei den Krokodilen steht auf Position 2."
    )


def test_same_position_constraint_validation_and_matching() -> None:
    child = Item("Mia")
    theme = Item("salsa", category_id="dance_style")
    constraint = SamePositionConstraint(child, theme)
    assert constraint.matches(Assignment({child: Position(1), theme: Position(1)}))
    assert not constraint.matches(Assignment({child: Position(1), theme: Position(2)}))
    with pytest.raises(ValueError, match="distinct"):
        SamePositionConstraint(child, child)
    with pytest.raises(ValueError, match="different categories"):
        SamePositionConstraint(child, Item("Emma"))
    with pytest.raises(TypeError, match="Item instances"):
        SamePositionConstraint("Mia", theme)  # type: ignore[arg-type]


@pytest.mark.parametrize("language", ["en", "de"])
def test_generated_pdfs_do_not_expose_internal_theme_ids(tmp_path, language: str) -> None:
    puzzle = PuzzleGenerator(
        random_source=random.Random(4), difficulty="easy", theme="beach_day"
    ).generate(create_template())
    puzzle_path = tmp_path / f"puzzle_{language}.pdf"
    solution_path = tmp_path / f"solution_{language}.pdf"
    generator = PdfGenerator(language=language)

    generator.create_puzzle_pdf(puzzle, puzzle_path)
    generator.create_solution_pdf(puzzle, solution_path)

    combined = puzzle_path.read_bytes() + solution_path.read_bytes()
    for internal_id in INTERNAL_IDS:
        assert internal_id.encode() not in combined
    if language == "de":
        assert "ß".encode() not in combined
