from __future__ import annotations

from copy import deepcopy

import pytest

from logical_puzzle_generator.constraints import AdjacentConstraint, LeftOfConstraint
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.metadata import Metadata
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution
from logical_puzzle_generator.pdf.generator import PdfGenerator


def sample_puzzle() -> Puzzle:
    aurelia = Item("Aurelia")
    emma = Item("Emma")
    lara = Item("Lara")
    mia = Item("Mia")
    assignment = Assignment(
        {
            lara: Position(3),
            aurelia: Position(1),
            mia: Position(4),
            emma: Position(2),
        }
    )
    left_of = LeftOfConstraint(aurelia, emma)
    adjacent = AdjacentConstraint(lara, mia)
    return Puzzle(
        items=[aurelia, emma, lara, mia],
        constraints=[left_of, adjacent],
        clues=[
            Clue(ClueType.LEFT_OF, "Aurelia is somewhere left of Emma.", left_of),
            Clue(ClueType.ADJACENT, "Lara is next to Mia.", adjacent),
        ],
        metadata=Metadata(title="Tennis Training", theme="Tennis", difficulty=1),
        solution=Solution(assignment),
    )


def pdf_text_bytes(path) -> str:
    return path.read_bytes().decode("latin-1", errors="ignore")


def test_create_puzzle_pdf_writes_non_empty_pdf_with_clue_text(tmp_path) -> None:
    path = tmp_path / "nested" / "puzzle.pdf"

    PdfGenerator().create_puzzle_pdf(sample_puzzle(), path)

    assert path.exists()
    assert path.stat().st_size > 0
    text = pdf_text_bytes(path)
    assert "Aurelia is somewhere left of Emma" in text
    assert "LeftOfConstraint" not in text


def test_create_solution_pdf_writes_non_empty_pdf(tmp_path) -> None:
    path = tmp_path / "solutions" / "solution.pdf"

    PdfGenerator().create_solution_pdf(sample_puzzle(), path)

    assert path.exists()
    assert path.stat().st_size > 0
    text = pdf_text_bytes(path)
    assert "Solution" in text
    assert "Aurelia" in text


def test_solution_rows_follow_position_order() -> None:
    rows = PdfGenerator()._text_renderer.render_solution_rows(sample_puzzle())

    assert rows == [
        ("1", "Aurelia"),
        ("2", "Emma"),
        ("3", "Lara"),
        ("4", "Mia"),
    ]


def test_pdf_generation_does_not_mutate_puzzle(tmp_path) -> None:
    puzzle = sample_puzzle()
    original = deepcopy(puzzle)

    generator = PdfGenerator()
    generator.create_puzzle_pdf(puzzle, tmp_path / "puzzle.pdf")
    generator.create_solution_pdf(puzzle, tmp_path / "solution.pdf")

    assert puzzle == original


def test_solution_pdf_requires_solution(tmp_path) -> None:
    puzzle = sample_puzzle()
    puzzle.solution = None

    with pytest.raises(ValueError, match="no Solution"):
        PdfGenerator().create_solution_pdf(puzzle, tmp_path / "solution.pdf")


def test_compatibility_create_method_writes_puzzle_pdf(tmp_path) -> None:
    path = tmp_path / "puzzle.pdf"

    PdfGenerator().create(sample_puzzle(), path)

    assert path.exists()
    assert path.stat().st_size > 0


def test_puzzle_pdf_contains_varied_human_readable_clue_text(tmp_path) -> None:
    import random

    from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
    from logical_puzzle_generator.pdf.generator import PdfGenerator
    from logical_puzzle_generator.themes.tennis import create_template

    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())
    output = tmp_path / "varied-puzzle.pdf"

    PdfGenerator().create_puzzle_pdf(puzzle, output)

    pdf_text = output.read_bytes().decode("latin-1")
    for clue in puzzle.clues:
        assert clue.text in pdf_text
    assert "DirectLeftOfConstraint" not in pdf_text
    assert "DirectRightOfConstraint" not in pdf_text
