from __future__ import annotations

import argparse
from pathlib import Path

from logical_puzzle_generator.cli import (
    parse_language_argument,
    parse_puzzle_book_difficulty_argument,
)
from logical_puzzle_generator.generator import Difficulty, PuzzleBookDifficultyMode
from logical_puzzle_generator.generator.puzzle_book import PuzzleBook, PuzzleBookGenerator
from logical_puzzle_generator.localization import Language, TranslationCatalog, parse_language
from logical_puzzle_generator.random_streams import derived_random
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.themes.registry import (
    DEFAULT_THEME_ID,
    DEFAULT_THEME_REGISTRY,
    RANDOM_THEME_ID,
)

DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_THEME_PAGE_COUNT = 8
DEFAULT_PUZZLE_BOOK_PATH = DEFAULT_OUTPUT_DIR / "puzzle_book.pdf"
DEFAULT_PUZZLE_BOOK_SOLUTION_PATH = DEFAULT_OUTPUT_DIR / "puzzle_book_solution.pdf"


def _validate_theme_page_count(theme_page_count: int) -> int:
    if not isinstance(theme_page_count, int) or isinstance(theme_page_count, bool):
        raise TypeError("Theme page count must be a non-negative integer.")
    if theme_page_count < 0:
        raise ValueError("Theme page count must not be negative.")
    return theme_page_count


def create_puzzle_book(
    *,
    theme_page_count: int = DEFAULT_THEME_PAGE_COUNT,
    puzzle_path: str | Path = DEFAULT_PUZZLE_BOOK_PATH,
    solution_path: str | Path = DEFAULT_PUZZLE_BOOK_SOLUTION_PATH,
    theme: str | None = None,
    difficulty: Difficulty | PuzzleBookDifficultyMode | str = Difficulty.EASY,
    language: Language | str = Language.ENGLISH,
    seed: int | None = None,
) -> PuzzleBook:
    theme_page_count = _validate_theme_page_count(theme_page_count)
    language = parse_language(language)
    generator = PuzzleBookGenerator(
        seed=seed,
        difficulty=difficulty,
        theme=theme or DEFAULT_THEME_ID,
    )
    book = generator.generate(theme_page_count=theme_page_count)
    pdf_random = derived_random(seed, "puzzle_book.pdf") if seed is not None else None
    pdf = PdfGenerator(language=language, random_source=pdf_random)
    pdf.create_puzzle_book_pdf(book, puzzle_path)
    pdf.create_puzzle_book_solution_pdf(book, solution_path)
    return book


def _parse_pages_argument(value: str) -> int:
    try:
        return _validate_theme_page_count(int(value))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def main(argv: list[str] | None = None) -> PuzzleBook:
    parser = argparse.ArgumentParser(description="Generate complete PuzzleBook PDFs.")
    parser.add_argument(
        "--theme",
        default=None,
        choices=(*DEFAULT_THEME_REGISTRY.supported_theme_ids(), RANDOM_THEME_ID),
        help="PuzzleBook theme. Omit for tennis_training; use random for seeded random selection.",
    )
    parser.add_argument(
        "--pages",
        type=_parse_pages_argument,
        default=DEFAULT_THEME_PAGE_COUNT,
        help="Number of Theme pages; excludes the Position page and summary page.",
    )
    parser.add_argument(
        "--difficulty",
        type=parse_puzzle_book_difficulty_argument,
        default=Difficulty.EASY,
        help="PuzzleBook difficulty: easy, medium, hard, or mixed. Defaults to easy; mixed creates a balanced deterministic mix across the Position and Theme pages.",
    )
    parser.add_argument(
        "--language",
        type=parse_language_argument,
        default=Language.ENGLISH,
        help="PDF language: en or de.",
    )
    parser.add_argument(
        "--puzzle-path",
        type=Path,
        default=DEFAULT_PUZZLE_BOOK_PATH,
        help="PuzzleBook puzzle PDF path.",
    )
    parser.add_argument(
        "--solution-path",
        type=Path,
        default=DEFAULT_PUZZLE_BOOK_SOLUTION_PATH,
        help="PuzzleBook solution PDF path.",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Optional integer seed for deterministic generation."
    )
    args = parser.parse_args(argv)
    book = create_puzzle_book(
        theme_page_count=args.pages,
        puzzle_path=args.puzzle_path,
        solution_path=args.solution_path,
        theme=args.theme,
        difficulty=args.difficulty,
        language=args.language,
        seed=args.seed,
    )
    catalog = TranslationCatalog(parse_language(args.language))
    print(f"{catalog.label('puzzle_written')}: {args.puzzle_path}")
    print(f"{catalog.label('solution_written')}: {args.solution_path}")
    return book


if __name__ == "__main__":
    main()
