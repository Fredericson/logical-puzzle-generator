from __future__ import annotations

import argparse
from pathlib import Path

from logical_puzzle_generator.generator import Difficulty
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.localization import (
    Language,
    TranslationCatalog,
    parse_language,
)
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
    language: Language | str = Language.ENGLISH,
    difficulty: Difficulty | str | None = None,
) -> Puzzle:
    """
    Generate Aurelia's Tennis puzzle and write puzzle and solution PDFs.

    If difficulty is None, Easy, Medium, or Hard is selected randomly.
    Otherwise difficulty is selected with "easy", "medium", "hard", or the
    matching Difficulty enum value.
    """
    number = _validate_number(number)
    language = parse_language(language)
    output_dir = DEFAULT_OUTPUT_DIR
    puzzle_path = Path(puzzle_path) if puzzle_path is not None else output_dir / f"puzzle_{number}.pdf"
    solution_path = (
        Path(solution_path)
        if solution_path is not None
        else output_dir / f"puzzle_{number}_solution.pdf"
    )

    template = create_template()
    puzzle = PuzzleGenerator(difficulty=difficulty).generate(template)
    pdf_generator = PdfGenerator(language=language)
    pdf_generator.create_puzzle_pdf(puzzle, puzzle_path)
    pdf_generator.create_solution_pdf(puzzle, solution_path)
    return puzzle


def _parse_difficulty_argument(value: str) -> Difficulty:
    try:
        from logical_puzzle_generator.generator import DifficultyPolicy

        return DifficultyPolicy().normalize(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parse_language_argument(value: str) -> Language:
    try:
        return parse_language(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def main(argv: list[str] | None = None) -> Puzzle:
    parser = argparse.ArgumentParser(description="Generate Aurelia's Tennis puzzle PDFs.")
    parser.add_argument(
        "--number",
        type=int,
        default=DEFAULT_PUZZLE_NUMBER,
        help="Positive puzzle number used in output PDF filenames.",
    )
    parser.add_argument(
        "--language",
        type=_parse_language_argument,
        default=Language.ENGLISH,
        help="PDF language: en (English, default) or de (German).",
    )
    parser.add_argument(
        "--difficulty",
        type=_parse_difficulty_argument,
        default=None,
        help="Puzzle difficulty: easy, medium, or hard. Omit to choose randomly.",
    )
    args = parser.parse_args(argv)
    number = _validate_number(args.number)
    language = parse_language(args.language)
    difficulty = args.difficulty
    puzzle_path = DEFAULT_OUTPUT_DIR / f"puzzle_{number}.pdf"
    solution_path = DEFAULT_OUTPUT_DIR / f"puzzle_{number}_solution.pdf"
    puzzle = create_puzzle(
        number=number,
        puzzle_path=puzzle_path,
        solution_path=solution_path,
        language=language,
        difficulty=difficulty,
    )
    catalog = TranslationCatalog(language)
    print(f"{catalog.label('puzzle_written')}: {puzzle_path}")
    print(f"{catalog.label('solution_written')}: {solution_path}")
    return puzzle


if __name__ == "__main__":
    main()
