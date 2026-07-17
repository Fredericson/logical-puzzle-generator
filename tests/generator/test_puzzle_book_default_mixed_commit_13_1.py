from __future__ import annotations

from logical_puzzle_generator.generator.puzzle_book import PuzzleBookGenerator


def _difficulties(book):
    return [p.metadata.difficulty for p in book.pages if p.metadata]


def test_programmatic_puzzle_book_default_is_mixed() -> None:
    book = PuzzleBookGenerator(theme="tennis_training", seed=42).generate(theme_page_count=2)
    assert _difficulties(book) == [3, 2, 1]


def test_programmatic_none_puzzle_book_default_is_mixed() -> None:
    book = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty=None).generate(
        theme_page_count=2
    )
    assert _difficulties(book) == [3, 2, 1]


def test_explicit_uniform_books_remain_uniform() -> None:
    for difficulty, value in (("easy", 1), ("medium", 2), ("hard", 3)):
        book = PuzzleBookGenerator(
            theme="tennis_training", seed=42, difficulty=difficulty
        ).generate(theme_page_count=2)
        assert _difficulties(book) == [value, value, value]
