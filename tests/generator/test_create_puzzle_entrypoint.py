from __future__ import annotations

from logical_puzzle_generator.create_puzzle import create_puzzle
from logical_puzzle_generator.model.puzzle import Puzzle


def test_tennis_workflow_creates_puzzle_and_solution_pdfs(tmp_path) -> None:
    puzzle_path = tmp_path / "generated" / "puzzle_3.pdf"
    solution_path = tmp_path / "generated" / "puzzle_3_solution.pdf"

    puzzle = create_puzzle(puzzle_path=puzzle_path, solution_path=solution_path)

    assert isinstance(puzzle, Puzzle)
    assert puzzle.metadata is not None
    assert puzzle.metadata.theme == "Tennis"
    assert puzzle_path.exists()
    assert solution_path.exists()
    assert puzzle_path.stat().st_size > 0
    assert solution_path.stat().st_size > 0


def test_create_puzzle_uses_configurable_number_paths(tmp_path) -> None:
    puzzle = create_puzzle(number=12, puzzle_path=tmp_path / "puzzle_12.pdf", solution_path=tmp_path / "puzzle_12_solution.pdf")

    assert isinstance(puzzle, Puzzle)
    assert (tmp_path / "puzzle_12.pdf").exists()
    assert (tmp_path / "puzzle_12_solution.pdf").exists()


def test_create_puzzle_rejects_non_positive_number() -> None:
    import pytest

    with pytest.raises(ValueError, match="positive integer"):
        create_puzzle(number=0)


def test_create_puzzle_accepts_string_difficulty(tmp_path) -> None:
    puzzle = create_puzzle(
        difficulty="hard",
        puzzle_path=tmp_path / "p.pdf",
        solution_path=tmp_path / "s.pdf",
    )

    assert puzzle.metadata is not None
    assert puzzle.metadata.difficulty == 3


def test_create_puzzle_accepts_typed_difficulty(tmp_path) -> None:
    from logical_puzzle_generator.generator import Difficulty

    puzzle = create_puzzle(
        difficulty=Difficulty.EASY,
        puzzle_path=tmp_path / "p.pdf",
        solution_path=tmp_path / "s.pdf",
    )

    assert puzzle.metadata is not None
    assert puzzle.metadata.difficulty == 1


def test_create_puzzle_rejects_invalid_difficulty(tmp_path) -> None:
    import pytest

    with pytest.raises(ValueError, match="Unsupported difficulty"):
        create_puzzle(
            difficulty="beginner",
            puzzle_path=tmp_path / "p.pdf",
            solution_path=tmp_path / "s.pdf",
        )


def test_cli_accepts_difficulty_values(tmp_path, monkeypatch) -> None:
    from logical_puzzle_generator.create_puzzle import main

    monkeypatch.chdir(tmp_path)

    for number, difficulty, metadata in [(21, "easy", 1), (22, "medium", 2), (23, "hard", 3)]:
        puzzle = main(["--number", str(number), "--difficulty", difficulty])
        assert puzzle.metadata is not None
        assert puzzle.metadata.difficulty == metadata
        assert (tmp_path / "output" / f"puzzle_{number}.pdf").exists()
        assert (tmp_path / "output" / f"puzzle_{number}_solution.pdf").exists()


def test_cli_rejects_invalid_difficulty() -> None:
    import pytest
    from logical_puzzle_generator.create_puzzle import main

    with pytest.raises(SystemExit):
        main(["--difficulty", "beginner"])
