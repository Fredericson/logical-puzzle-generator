from __future__ import annotations

import argparse
from pathlib import Path

from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.themes.tennis import create_template


DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_PUZZLE_NUMBER = 3


def _validate_number(number: int) -> int:
    if not isinstance(number, int) or isinstance(number, bool):
        raise TypeError("Puzzle number must be a positive integer.")
    if number < 1:
        raise ValueError("Puzzle number must be a positive integer.")
    return number


def create_puzzle(
    number: int = DEFAULT_PUZZLE_NUMBER,
    puzzle_path: str | Path | None = None,
    solution_path: str | Path | None = None,
) -> Puzzle:
    """
    Generate Aurelia's Tennis puzzle and write puzzle and solution PDFs.
    """
    number = _validate_number(number)
    output_dir = DEFAULT_OUTPUT_DIR
    puzzle_path = Path(puzzle_path) if puzzle_path is not None else output_dir / f"puzzle_{number}.pdf"
    solution_path = (
        Path(solution_path)
        if solution_path is not None
        else output_dir / f"puzzle_{number}_solution.pdf"
    )

    template = create_template()
    puzzle = PuzzleGenerator().generate(template)
    pdf_generator = PdfGenerator()
    pdf_generator.create_puzzle_pdf(puzzle, puzzle_path)
    pdf_generator.create_solution_pdf(puzzle, solution_path)
    return puzzle


def main(argv: list[str] | None = None) -> Puzzle:
    parser = argparse.ArgumentParser(description="Generate Aurelia's Tennis puzzle PDFs.")
    parser.add_argument(
        "--number",
        type=int,
        default=DEFAULT_PUZZLE_NUMBER,
        help="Positive puzzle number used in output PDF filenames.",
    )
    args = parser.parse_args(argv)
    number = _validate_number(args.number)
    puzzle_path = DEFAULT_OUTPUT_DIR / f"puzzle_{number}.pdf"
    solution_path = DEFAULT_OUTPUT_DIR / f"puzzle_{number}_solution.pdf"
    puzzle = create_puzzle(number=number, puzzle_path=puzzle_path, solution_path=solution_path)
    print(f"Puzzle PDF written to: {puzzle_path}")
    print(f"Solution PDF written to: {solution_path}")
    return puzzle


if __name__ == "__main__":
    main()
