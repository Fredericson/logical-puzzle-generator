from __future__ import annotations

from copy import deepcopy
import random

import pytest

from logical_puzzle_generator.constraints import AdjacentConstraint, LeftOfConstraint
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.metadata import Metadata
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.themes.tennis import create_template


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
    assert "Aurelia" in text
    assert "Emma" in text
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
    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())
    output = tmp_path / "varied-puzzle.pdf"

    PdfGenerator(random_source=random.Random(7)).create_puzzle_pdf(puzzle, output)

    pdf_text = output.read_bytes().decode("latin-1")
    for clue in puzzle.clues:
        assert clue.constraint.__class__.__name__ not in pdf_text
    assert "DirectLeftOfConstraint" not in pdf_text
    assert "DirectRightOfConstraint" not in pdf_text


def pdf_page_count(path) -> int:
    text = pdf_text_bytes(path)
    return text.count("/Type /Page") - text.count("/Type /Pages")


def test_puzzle_lineup_contains_four_visual_position_placeholders() -> None:
    lineup = PdfGenerator()._lineup(sample_puzzle())

    slots = lineup.layout_slots()

    assert [slot.position for slot in slots] == [1, 2, 3, 4]
    assert [slot.label for slot in slots] == ["", "", "", ""]
    assert all(left.x < right.x for left, right in zip(slots, slots[1:]))


def test_puzzle_lineup_contains_four_empty_writable_boxes() -> None:
    lineup = PdfGenerator()._lineup(sample_puzzle())

    slots = lineup.layout_slots()

    assert len(slots) == 4
    assert all(slot.box_width >= 1.0 * 72 for slot in slots)
    assert all(slot.box_height >= 0.35 * 72 for slot in slots)
    assert all(slot.label == "" for slot in slots)


def test_solution_pdf_contains_solved_names_in_position_order(tmp_path) -> None:
    path = tmp_path / "solution.pdf"

    PdfGenerator().create_solution_pdf(sample_puzzle(), path)

    text = pdf_text_bytes(path)
    assert text.index("Aurelia") < text.index("Emma") < text.index("Lara") < text.index("Mia")


def test_german_pdf_contains_child_facing_labels(tmp_path) -> None:
    path = tmp_path / "raetsel.pdf"

    PdfGenerator(language="de").create_puzzle_pdf(sample_puzzle(), path)

    text = pdf_text_bytes(path)
    assert "Tennistraining" in text
    assert "Thema" in text
    assert "Schwierigkeit" in text
    assert "Hinweise" in text
    assert "Trage die Namen ein" in text
    assert "Verf\\374gbare Namen" in text
    assert "Players / Items" not in text


def test_english_pdf_remains_supported(tmp_path) -> None:
    path = tmp_path / "puzzle.pdf"

    PdfGenerator(language="en").create_puzzle_pdf(sample_puzzle(), path)

    text = pdf_text_bytes(path)
    assert "Theme" in text
    assert "Difficulty" in text
    assert "Clues" in text
    assert "Write the names" in text
    assert "Available Names" in text


def test_puzzle_lineup_does_not_reveal_solution_in_name_boxes() -> None:
    puzzle = sample_puzzle()

    lineup = PdfGenerator()._lineup(puzzle)

    assert [slot.label for slot in lineup.layout_slots()] == ["", "", "", ""]
    assert PdfGenerator()._solution_labels(puzzle) == ["Aurelia", "Emma", "Lara", "Mia"]


def test_solution_labels_use_puzzle_solution_assignment() -> None:
    puzzle = sample_puzzle()
    items = {item.name: item for item in puzzle.items}
    puzzle.solution = Solution(
        Assignment(
            {
                items["Mia"]: Position(1),
                items["Lara"]: Position(2),
                items["Emma"]: Position(3),
                items["Aurelia"]: Position(4),
            }
        )
    )

    assert PdfGenerator()._solution_labels(puzzle) == ["Mia", "Lara", "Emma", "Aurelia"]


def test_four_player_tennis_pdfs_remain_one_page(tmp_path) -> None:
    puzzle_path = tmp_path / "puzzle.pdf"
    solution_path = tmp_path / "solution.pdf"
    generator = PdfGenerator()

    generator.create_puzzle_pdf(sample_puzzle(), puzzle_path)
    generator.create_solution_pdf(sample_puzzle(), solution_path)

    assert pdf_page_count(puzzle_path) == 1
    assert pdf_page_count(solution_path) == 1


def test_generated_pdf_files_are_non_empty(tmp_path) -> None:
    puzzle_path = tmp_path / "puzzle.pdf"
    solution_path = tmp_path / "solution.pdf"

    PdfGenerator().create_puzzle_pdf(sample_puzzle(), puzzle_path)
    PdfGenerator().create_solution_pdf(sample_puzzle(), solution_path)

    assert puzzle_path.stat().st_size > 0
    assert solution_path.stat().st_size > 0


def test_unsupported_pdf_language_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported language"):
        PdfGenerator(language="fr")


@pytest.mark.parametrize(
    ("language", "difficulty", "expected"),
    [
        ("en", 1, "Difficulty: Easy"),
        ("en", 2, "Difficulty: Medium"),
        ("en", 3, "Difficulty: Hard"),
        ("en", 4, "Difficulty: Hard"),
        ("de", 1, "Schwierigkeit: Leicht"),
        ("de", 2, "Schwierigkeit: Mittel"),
        ("de", 3, "Schwierigkeit: Schwierig"),
        ("de", 4, "Schwierigkeit: Schwierig"),
    ],
)
def test_pdf_uses_localized_child_facing_difficulty_labels(
    tmp_path, language, difficulty, expected
) -> None:
    puzzle = sample_puzzle()
    puzzle.metadata.difficulty = difficulty
    path = tmp_path / f"puzzle-{language}-{difficulty}.pdf"

    PdfGenerator(language=language).create_puzzle_pdf(puzzle, path)

    text = pdf_text_bytes(path)
    assert expected in text


def test_generated_pdf_shows_localized_calculated_difficulty(tmp_path) -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(1)).generate(create_template())
    assert puzzle.metadata is not None
    assert puzzle.metadata.difficulty == 1

    en_path = tmp_path / "generated-en.pdf"
    de_path = tmp_path / "generated-de.pdf"
    PdfGenerator(language="en").create_puzzle_pdf(puzzle, en_path)
    PdfGenerator(language="de").create_puzzle_pdf(puzzle, de_path)

    assert "Difficulty: Easy" in pdf_text_bytes(en_path)
    assert "Schwierigkeit: Leicht" in pdf_text_bytes(de_path)


def test_missing_difficulty_omits_difficulty_line(tmp_path) -> None:
    puzzle = sample_puzzle()
    puzzle.metadata.difficulty = None
    path = tmp_path / "puzzle.pdf"

    PdfGenerator().create_puzzle_pdf(puzzle, path)

    text = pdf_text_bytes(path)
    assert "Difficulty" not in text


def test_raw_numeric_difficulty_is_not_rendered_in_puzzle_pdf(tmp_path) -> None:
    puzzle = sample_puzzle()
    puzzle.metadata.difficulty = 1
    path = tmp_path / "puzzle.pdf"

    PdfGenerator().create_puzzle_pdf(puzzle, path)

    text = pdf_text_bytes(path)
    assert "Difficulty: Easy" in text
    assert "Difficulty: 1" not in text


def test_raw_numeric_difficulty_is_not_rendered_in_solution_pdf(tmp_path) -> None:
    puzzle = sample_puzzle()
    puzzle.metadata.difficulty = 1
    path = tmp_path / "solution.pdf"

    PdfGenerator().create_solution_pdf(puzzle, path)

    text = pdf_text_bytes(path)
    assert "Difficulty: Easy" in text
    assert "Difficulty: 1" not in text


@pytest.mark.parametrize("difficulty", [0, -1, 1.5, "1", True])
def test_unsupported_difficulty_values_fail_clearly(tmp_path, difficulty) -> None:
    puzzle = sample_puzzle()
    puzzle.metadata.difficulty = difficulty

    with pytest.raises(ValueError, match="Unsupported difficulty value"):
        PdfGenerator().create_puzzle_pdf(puzzle, tmp_path / "puzzle.pdf")


def test_pdf_generation_with_localized_difficulty_remains_one_page(tmp_path) -> None:
    puzzle_path = tmp_path / "puzzle.pdf"
    solution_path = tmp_path / "solution.pdf"

    PdfGenerator(language="de").create_puzzle_pdf(sample_puzzle(), puzzle_path)
    PdfGenerator(language="de").create_solution_pdf(sample_puzzle(), solution_path)

    assert pdf_page_count(puzzle_path) == 1
    assert pdf_page_count(solution_path) == 1
