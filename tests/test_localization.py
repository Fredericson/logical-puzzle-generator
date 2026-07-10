from __future__ import annotations

import random
from copy import deepcopy

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
from logical_puzzle_generator.create_puzzle import create_puzzle, main
from logical_puzzle_generator.engine.validator import Validator
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.localization import Language, parse_language
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.themes.tennis import create_template


def render_de(constraint, clue_type: ClueType, item_count: int = 4) -> str:
    clue = Clue(clue_type, "English compatibility text.", constraint)
    return ClueTextRenderer(Language.GERMAN, item_count=item_count).render_clue(clue)


def pdf_text(path) -> str:
    return path.read_bytes().decode("latin-1", errors="ignore")


def test_english_clue_text_remains_unchanged() -> None:
    emma = Item("Emma")
    aurelia = Item("Aurelia")
    constraint = LeftOfConstraint(emma, aurelia)
    clue = Clue(ClueType.LEFT_OF, "Emma stands left of Aurelia.", constraint)

    assert ClueTextRenderer(Language.ENGLISH).render_clue(clue) == "Emma stands left of Aurelia."


@pytest.mark.parametrize(
    ("constraint", "clue_type", "expected"),
    [
        (FixedPositionConstraint(Item("Emma"), Position(1)), ClueType.FIXED_POSITION, "Emma steht ganz links."),
        (FixedPositionConstraint(Item("Mia"), Position(4)), ClueType.FIXED_POSITION, "Mia steht ganz rechts."),
        (DirectLeftOfConstraint(Item("Emma"), Item("Aurelia")), ClueType.DIRECT_LEFT_OF, "Emma steht direkt links von Aurelia."),
        (LeftOfConstraint(Item("Emma"), Item("Aurelia")), ClueType.LEFT_OF, "Emma steht links von Aurelia."),
        (DirectRightOfConstraint(Item("Aurelia"), Item("Emma")), ClueType.DIRECT_RIGHT_OF, "Aurelia steht direkt rechts von Emma."),
        (RightOfConstraint(Item("Aurelia"), Item("Emma")), ClueType.RIGHT_OF, "Aurelia steht rechts von Emma."),
        (AdjacentConstraint(Item("Lara"), Item("Mia")), ClueType.ADJACENT, "Lara steht neben Mia."),
    ],
)
def test_german_clue_wording(constraint, clue_type, expected) -> None:
    assert render_de(constraint, clue_type) == expected


def test_cli_accepts_language_de_and_en(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    main(["--number", "3", "--language", "de"])
    main(["--number", "4", "--language", "en"])

    assert (tmp_path / "output" / "puzzle_3.pdf").exists()
    assert (tmp_path / "output" / "puzzle_3_solution.pdf").exists()
    assert (tmp_path / "output" / "puzzle_4.pdf").exists()
    assert (tmp_path / "output" / "puzzle_4_solution.pdf").exists()


def test_invalid_language_is_rejected_clearly() -> None:
    with pytest.raises(ValueError, match="Unsupported language"):
        parse_language("fr")
    with pytest.raises(SystemExit):
        main(["--language", "fr"])


def test_create_puzzle_language_writes_both_pdfs(tmp_path) -> None:
    puzzle = create_puzzle(
        number=3,
        puzzle_path=tmp_path / "puzzle.pdf",
        solution_path=tmp_path / "solution.pdf",
        language=Language.GERMAN,
    )

    assert (tmp_path / "puzzle.pdf").exists()
    assert (tmp_path / "solution.pdf").exists()
    assert Validator().has_unique_solution(puzzle)


def test_german_puzzle_pdf_contains_german_headings_and_clues_without_english_leaks(tmp_path) -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())
    path = tmp_path / "puzzle-de.pdf"

    PdfGenerator(language="de").create_puzzle_pdf(puzzle, path)

    text = pdf_text(path)
    assert "Tennistraining" in text
    assert "Thema" in text
    assert "Schwierigkeit" in text
    assert "Hinweise" in text
    assert "Position" in text
    assert "Antwort" in text
    assert "steht" in text
    assert "Theme" not in text
    assert "Difficulty" not in text
    assert "Clues" not in text
    assert "Solving Grid" not in text


def test_german_solution_pdf_contains_german_headings(tmp_path) -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())
    path = tmp_path / "solution-de.pdf"

    PdfGenerator(language="de").create_solution_pdf(puzzle, path)

    text = pdf_text(path)
    assert "Tennistraining" in text
    assert "Thema" in text
    assert "Schwierigkeit" in text
    assert "Position" in text
    assert "Hinweise" in text
    assert "Aurelia" in text
    assert "Theme" not in text
    assert "Solution" not in text


def test_german_pdf_generation_does_not_mutate_puzzle(tmp_path) -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())
    original = deepcopy(puzzle)

    PdfGenerator(language="de").create_puzzle_pdf(puzzle, tmp_path / "puzzle.pdf")
    PdfGenerator(language="de").create_solution_pdf(puzzle, tmp_path / "solution.pdf")

    assert puzzle == original


def test_clue_constraint_mapping_is_unchanged_by_localized_rendering() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())
    before = [(clue.clue_type, clue.constraint) for clue in puzzle.clues]

    ClueTextRenderer(Language.GERMAN, item_count=len(puzzle.items))
    rendered = PdfGenerator(language="de")._text_renderer.render_clues(
        puzzle.clues,
        item_count=len(puzzle.items),
    )

    assert len(rendered) == len(puzzle.clues) == len(puzzle.constraints)
    assert [(clue.clue_type, clue.constraint) for clue in puzzle.clues] == before


def test_seeded_generation_is_deterministic_regardless_of_output_language(tmp_path) -> None:
    puzzle_en = PuzzleGenerator(random_source=random.Random(11)).generate(create_template())
    puzzle_de = deepcopy(puzzle_en)

    PdfGenerator(language="en").create_puzzle_pdf(puzzle_en, tmp_path / "en.pdf")
    PdfGenerator(language="de").create_puzzle_pdf(puzzle_de, tmp_path / "de.pdf")

    assert puzzle_de == puzzle_en
    assert Validator().has_unique_solution(puzzle_en)
