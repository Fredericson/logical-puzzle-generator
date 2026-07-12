from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.clue_text_renderer import ClueTextRenderer
from logical_puzzle_generator.constraints import (
    AdjacentConstraint,
    DirectLeftOfConstraint,
    DirectRightOfConstraint,
    FixedPositionConstraint,
    LeftOfConstraint,
    RightOfConstraint,
)
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.template_catalog import TemplateCatalog


def _clue(constraint) -> Clue:
    return Clue(ClueType.LEFT_OF, "legacy clue text", constraint)


def _items() -> tuple[Item, Item]:
    return Item("Mia"), Item("Emma")


def _constraints():
    mia, emma = _items()
    return [
        FixedPositionConstraint(mia, Position(2)),
        DirectLeftOfConstraint(mia, emma),
        LeftOfConstraint(mia, emma),
        DirectRightOfConstraint(emma, mia),
        RightOfConstraint(emma, mia),
        AdjacentConstraint(mia, emma),
    ]


@pytest.mark.parametrize("language", ["en", "de"])
def test_every_constraint_type_has_multiple_unique_wording_templates(language: str) -> None:
    catalog = TemplateCatalog(language)

    for constraint_type in TemplateCatalog.visible_constraint_types():
        templates = catalog.template_texts_for(constraint_type)
        assert len(templates) >= 3
        assert len(templates) == len(set(templates))


def test_identical_seed_produces_identical_wording() -> None:
    clues = [_clue(constraint) for constraint in _constraints()]

    first = [ClueTextRenderer(random_source=random.Random(42)).render_clue(clue) for clue in clues]
    second = [ClueTextRenderer(random_source=random.Random(42)).render_clue(clue) for clue in clues]

    assert first == second


def test_different_seeds_vary_wording() -> None:
    clue = _clue(LeftOfConstraint(Item("Mia"), Item("Emma")))

    variants = {
        ClueTextRenderer(random_source=random.Random(seed)).render_clue(clue) for seed in range(20)
    }

    assert len(variants) > 1


def test_german_wording_contains_no_sharp_s() -> None:
    for constraint in _constraints():
        for seed in range(10):
            text = ClueTextRenderer("de", random_source=random.Random(seed)).render_clue(
                _clue(constraint)
            )
            assert "ß" not in text


def test_placeholders_are_substituted_and_sentences_are_complete() -> None:
    for language in ("en", "de"):
        for constraint in _constraints():
            text = ClueTextRenderer(language, random_source=random.Random(0)).render_clue(
                _clue(constraint)
            )
            assert "{" not in text
            assert "}" not in text
            assert text.endswith(".")
            assert "  " not in text


def test_wording_preserves_identical_constraint_semantics() -> None:
    mia = Item("Mia")
    emma = Item("Emma")
    valid_assignment = Assignment({mia: Position(1), emma: Position(3)})
    invalid_assignment = Assignment({mia: Position(3), emma: Position(1)})
    constraint = LeftOfConstraint(mia, emma)
    clue = _clue(constraint)

    rendered = {
        ClueTextRenderer(random_source=random.Random(seed)).render_clue(clue) for seed in range(20)
    }

    assert len(rendered) > 1
    assert constraint.matches(valid_assignment)
    assert not constraint.matches(invalid_assignment)
    assert clue.constraint is constraint


def test_every_catalog_wording_is_grammatically_expected() -> None:
    expected_terms = {
        "en": ("stands", "stand", "Position"),
        "de": ("steht", "stehen", "Position"),
    }

    for language, terms in expected_terms.items():
        catalog = TemplateCatalog(language)
        for constraint_type in TemplateCatalog.visible_constraint_types():
            for template in catalog.template_texts_for(constraint_type):
                assert template[0].isupper() or template.startswith("{")
                assert template.endswith(".")
                assert any(term in template for term in terms)
