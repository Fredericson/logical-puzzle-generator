from __future__ import annotations

from collections import Counter
import re

import pytest

from logical_puzzle_generator.create_puzzle_book import create_puzzle_book, main


def _pdf_page_marker_count(path) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", path.read_bytes()))


def test_create_puzzle_book_api_writes_custom_paths(tmp_path) -> None:
    puzzle_path = tmp_path / "book.pdf"
    solution_path = tmp_path / "solution.pdf"
    book = create_puzzle_book(
        theme_page_count=1,
        puzzle_path=puzzle_path,
        solution_path=solution_path,
        theme="tennis_training",
        difficulty="easy",
        language="en",
        seed=42,
    )
    assert puzzle_path.exists()
    assert solution_path.exists()
    assert len(book.theme_puzzles) == 1


def test_create_puzzle_book_cli_defaults_and_languages(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(
        [
            "--theme",
            "tennis_training",
            "--pages",
            "1",
            "--difficulty",
            "easy",
            "--language",
            "de",
            "--seed",
            "42",
        ]
    )
    assert (tmp_path / "output" / "puzzle_book.pdf").exists()
    assert (tmp_path / "output" / "puzzle_book_solution.pdf").exists()


def test_create_puzzle_book_cli_rejects_invalid_pages() -> None:
    with pytest.raises(SystemExit):
        main(["--pages", "-1"])


def test_create_puzzle_book_seed_is_deterministic(tmp_path) -> None:
    first = create_puzzle_book(
        theme_page_count=2,
        puzzle_path=tmp_path / "a.pdf",
        solution_path=tmp_path / "as.pdf",
        theme="random",
        difficulty="easy",
        seed=9,
    )
    second = create_puzzle_book(
        theme_page_count=2,
        puzzle_path=tmp_path / "b.pdf",
        solution_path=tmp_path / "bs.pdf",
        theme="random",
        difficulty="easy",
        seed=9,
    )
    assert first.theme_id == second.theme_id
    assert [p.metadata.selected_theme_value_ids for p in first.theme_puzzles if p.metadata] == [
        p.metadata.selected_theme_value_ids for p in second.theme_puzzles if p.metadata
    ]


def _book_signature(book):
    return (
        book.theme_id,
        tuple(child.name for child in book.children),
        tuple(
            (child.name, book.position_puzzle.solution.assignment.position_of(child).index)
            for child in book.children
        ),
        tuple(
            puzzle.metadata.theme_category_id for puzzle in book.theme_puzzles if puzzle.metadata
        ),
        tuple(
            puzzle.metadata.theme_category_instance_id
            for puzzle in book.theme_puzzles
            if puzzle.metadata
        ),
        tuple(
            puzzle.metadata.selected_theme_value_ids
            for puzzle in book.theme_puzzles
            if puzzle.metadata
        ),
        tuple(
            tuple(type(constraint).__name__ for constraint in puzzle.constraints)
            for puzzle in book.theme_puzzles
        ),
        tuple(
            tuple(clue.clue_type.value for clue in puzzle.clues) for puzzle in book.theme_puzzles
        ),
        tuple(
            tuple(
                (item.name, puzzle.solution.assignment.position_of(item).index)
                for item in puzzle.logical_items
            )
            for puzzle in book.theme_puzzles
        ),
        book.summary_table,
    )


def test_create_puzzle_book_cli_custom_paths_and_english(tmp_path) -> None:
    puzzle_path = tmp_path / "custom" / "book.pdf"
    solution_path = tmp_path / "custom" / "solution.pdf"
    book = main(
        [
            "--theme",
            "tennis_training",
            "--pages",
            "1",
            "--difficulty",
            "easy",
            "--language",
            "en",
            "--puzzle-path",
            str(puzzle_path),
            "--solution-path",
            str(solution_path),
            "--seed",
            "7",
        ]
    )
    assert puzzle_path.exists()
    assert solution_path.exists()
    assert book.theme_id == "tennis_training"
    assert len(book.theme_puzzles) == 1


@pytest.mark.parametrize(
    "args",
    [
        ["--theme", "unknown"],
        ["--language", "fr"],
        ["--difficulty", "expert"],
        ["--seed", "nope"],
        ["--pages", "abc"],
    ],
)
def test_create_puzzle_book_cli_rejects_invalid_arguments(args) -> None:
    with pytest.raises(SystemExit):
        main(args)


def test_create_puzzle_book_seed_reproduces_full_domain_content(tmp_path) -> None:
    first = create_puzzle_book(
        theme_page_count=3,
        puzzle_path=tmp_path / "first.pdf",
        solution_path=tmp_path / "first_solution.pdf",
        theme="random",
        difficulty="easy",
        seed=12,
    )
    second = create_puzzle_book(
        theme_page_count=3,
        puzzle_path=tmp_path / "second.pdf",
        solution_path=tmp_path / "second_solution.pdf",
        theme="random",
        difficulty="easy",
        seed=12,
    )
    assert _book_signature(first) == _book_signature(second)


def test_create_puzzle_book_zero_theme_pages_is_intentional(tmp_path, monkeypatch) -> None:
    from reportlab.platypus import PageBreak, Table

    from logical_puzzle_generator.pdf.generator import PdfGenerator

    captured = {}

    def capture_build(self, output_path, story, *, page_count=None):
        captured[output_path.name] = story

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    book = create_puzzle_book(
        theme_page_count=0,
        puzzle_path=tmp_path / "zero_book.pdf",
        solution_path=tmp_path / "zero_solution.pdf",
        theme="tennis_training",
        difficulty="easy",
        seed=5,
    )
    assert len(book.theme_puzzles) == 0
    assert book.summary_table.rows == ()
    puzzle_story = captured["zero_book.pdf"]
    solution_story = captured["zero_solution.pdf"]
    assert sum(isinstance(flowable, PageBreak) for flowable in puzzle_story) == 1
    puzzle_summary = [flowable for flowable in puzzle_story if isinstance(flowable, Table)][-1]
    solution_summary = [flowable for flowable in solution_story if isinstance(flowable, Table)][-1]
    assert len(puzzle_summary._cellvalues) == 2
    assert len(solution_summary._cellvalues) == 2
    assert puzzle_summary._cellvalues[1][1:] == ["", "", "", ""]
    assert solution_summary._cellvalues[1][1:] == list(book.summary_table.child_names_by_position)


@pytest.mark.parametrize(("difficulty", "metadata"), [("easy", 1), ("medium", 2), ("hard", 3)])
def test_create_puzzle_book_cli_uniform_difficulty_applies_to_all_pages(
    tmp_path, difficulty, metadata
) -> None:
    puzzle_path = tmp_path / f"{difficulty}.pdf"
    solution_path = tmp_path / f"{difficulty}_solution.pdf"
    book = main(
        [
            "--theme",
            "tennis_training",
            "--pages",
            "1",
            "--difficulty",
            difficulty,
            "--language",
            "en",
            "--puzzle-path",
            str(puzzle_path),
            "--solution-path",
            str(solution_path),
            "--seed",
            "42",
        ]
    )

    assert puzzle_path.exists()
    assert solution_path.exists()
    assert [p.metadata.difficulty for p in book.pages if p.metadata] == [metadata, metadata]


def test_create_puzzle_book_cli_accepts_mixed_without_extra_difficulty_argument(tmp_path) -> None:
    puzzle_path = tmp_path / "mixed.pdf"
    solution_path = tmp_path / "mixed_solution.pdf"
    book = main(
        [
            "--theme",
            "tennis_training",
            "--pages",
            "2",
            "--difficulty",
            "mixed",
            "--language",
            "en",
            "--puzzle-path",
            str(puzzle_path),
            "--solution-path",
            str(solution_path),
            "--seed",
            "42",
        ]
    )

    assert puzzle_path.exists()
    assert solution_path.exists()
    assert {p.metadata.difficulty for p in book.pages if p.metadata} == {1, 2, 3}


def test_create_puzzle_book_cli_defaults_to_mixed(tmp_path) -> None:
    puzzle_path = tmp_path / "default.pdf"
    solution_path = tmp_path / "default_solution.pdf"
    book = main(
        [
            "--theme",
            "tennis_training",
            "--pages",
            "2",
            "--language",
            "en",
            "--puzzle-path",
            str(puzzle_path),
            "--solution-path",
            str(solution_path),
            "--seed",
            "42",
        ]
    )

    assert puzzle_path.exists()
    assert solution_path.exists()
    assert Counter(p.metadata.difficulty for p in book.pages if p.metadata) == Counter(
        {1: 1, 2: 1, 3: 1}
    )
    assert _pdf_page_marker_count(puzzle_path) == 4
    assert _pdf_page_marker_count(solution_path) == 1


def test_create_puzzle_book_cli_help_lists_mixed_default(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    for expected in ("easy", "medium", "hard", "mixed", "Defaults to mixed"):
        assert expected in help_text
    assert "Defaults to easy" not in help_text


def test_create_puzzle_book_cli_rejects_removed_position_difficulty_argument() -> None:
    with pytest.raises(SystemExit):
        main(["--difficulty", "mixed", "--position-difficulty", "easy"])
