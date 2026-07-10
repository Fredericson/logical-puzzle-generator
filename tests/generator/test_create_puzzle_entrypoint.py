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
