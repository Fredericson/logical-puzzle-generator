from __future__ import annotations

from pathlib import Path

from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.themes.tennis import create_template


DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_PUZZLE_PATH = DEFAULT_OUTPUT_DIR / "puzzle_3.pdf"
DEFAULT_SOLUTION_PATH = DEFAULT_OUTPUT_DIR / "puzzle_3_solution.pdf"


def create_puzzle(
    puzzle_path: str | Path = DEFAULT_PUZZLE_PATH,
    solution_path: str | Path = DEFAULT_SOLUTION_PATH,
) -> Puzzle:
    """
    Generate Aurelia's Tennis puzzle and write puzzle and solution PDFs.
    """
    template = create_template()
    puzzle = PuzzleGenerator().generate(template)
    pdf_generator = PdfGenerator()
    pdf_generator.create_puzzle_pdf(puzzle, puzzle_path)
    pdf_generator.create_solution_pdf(puzzle, solution_path)
    return puzzle


def main() -> Puzzle:
    puzzle = create_puzzle()
    print(f"Puzzle PDF written to: {DEFAULT_PUZZLE_PATH}")
    print(f"Solution PDF written to: {DEFAULT_SOLUTION_PATH}")
    return puzzle


if __name__ == "__main__":
    main()
