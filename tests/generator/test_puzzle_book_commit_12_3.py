import random

from reportlab.platypus import PageBreak, Table

from logical_puzzle_generator.generator.puzzle_book import PuzzleBookGenerator
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY


def _book(theme_page_count: int, seed: int = 0):
    return PuzzleBookGenerator(
        theme="tennis_training", random_source=random.Random(seed), difficulty="easy"
    ).generate(theme_page_count=theme_page_count)


def test_puzzle_book_reads_available_categories_from_selected_theme() -> None:
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    generator = PuzzleBookGenerator(theme="tennis_training", random_source=random.Random(0))

    assert generator.available_category_ids == tuple(category.id for category in theme.categories)
    assert "tournament_wins" not in generator.available_category_ids


def test_puzzle_book_selects_without_repetition_when_enough_categories() -> None:
    generator = PuzzleBookGenerator(theme="tennis_training", random_source=random.Random(1))

    selected = generator.select_category_ids(4)

    assert len(selected) == 4
    assert len(set(selected)) == 4
    assert set(selected) <= set(generator.available_category_ids)


def test_puzzle_book_reuses_categories_only_after_pool_is_exhausted() -> None:
    generator = PuzzleBookGenerator(theme="tennis_training", random_source=random.Random(2))
    available = generator.available_category_ids

    selected = generator.select_category_ids(len(available) + 3)

    assert len(selected) == len(available) + 3
    assert set(available) <= set(selected)
    assert set(selected) <= set(available)


def test_puzzle_book_has_position_first_and_theme_pages_afterwards() -> None:
    book = _book(theme_page_count=3, seed=3)

    assert book.pages[0] is book.position_puzzle
    assert len([book.position_puzzle]) == 1
    assert book.pages[1:] == book.theme_puzzles
    assert len(book.theme_puzzles) == 3
    assert book.position_puzzle.metadata is None


def test_children_are_identical_objects_on_every_page() -> None:
    book = _book(theme_page_count=2, seed=4)

    for puzzle in book.pages:
        page_children = tuple(
            item for item in puzzle.items if item.category_id == CHILDREN_CATEGORY_ID
        )
        assert page_children == book.children
        assert all(
            page_child is book_child
            for page_child, book_child in zip(page_children, book.children, strict=True)
        )


def test_every_theme_page_has_one_selected_category_and_one_theme() -> None:
    book = _book(theme_page_count=4, seed=5)
    registered = set(PuzzleBookGenerator(theme="tennis_training").available_category_ids)

    for puzzle in book.theme_puzzles:
        assert puzzle.metadata is not None
        assert puzzle.metadata.theme_id == book.theme_id
        assert puzzle.metadata.theme_category_id in registered
        theme_categories = [category for category in puzzle.categories if category.name != "Children"]
        assert len(theme_categories) == 1
        assert theme_categories[0].name == puzzle.metadata.theme_category_id


def test_repeated_categories_receive_distinct_instance_ids() -> None:
    generator = PuzzleBookGenerator(
        theme="tennis_training", random_source=random.Random(6), difficulty="easy"
    )
    page_count = len(generator.available_category_ids) + 5

    book = generator.generate(theme_page_count=page_count)
    by_category: dict[str, set[str]] = {}
    for puzzle in book.theme_puzzles:
        assert puzzle.metadata is not None
        by_category.setdefault(puzzle.metadata.theme_category_id or "", set()).add(
            puzzle.metadata.theme_category_instance_id or ""
        )

    assert any(len(instance_ids) > 1 for instance_ids in by_category.values())
    for category_id, instance_ids in by_category.items():
        assert len(instance_ids) == sum(
            1
            for puzzle in book.theme_puzzles
            if puzzle.metadata and puzzle.metadata.theme_category_id == category_id
        )


def test_summary_table_is_derived_from_book_pages_and_position_order() -> None:
    book = _book(theme_page_count=3, seed=7)

    summary = book.summary_table

    assert summary.child_ids == tuple(child.name for child in book.stable_children)
    assert len(summary.rows) == len(book.theme_puzzles)
    assert all(row.theme_category_id != "Position" for row in summary.rows)
    assert [row.theme_category_instance_id for row in summary.rows] == [
        puzzle.metadata.theme_category_instance_id
        for puzzle in book.theme_puzzles
        if puzzle.metadata
    ]
    assert all(len(row.value_ids_by_child) == len(book.children) for row in summary.rows)


def test_puzzle_book_pdfs_use_expected_page_shapes(monkeypatch, tmp_path) -> None:
    book = _book(theme_page_count=2, seed=8)
    captured: dict[str, list[object]] = {}

    def capture_build(self, output_path, story):
        captured[output_path.name] = story

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    pdf = PdfGenerator()

    pdf.create_puzzle_book_pdf(book, tmp_path / "puzzle_book.pdf")
    pdf.create_puzzle_book_solution_pdf(book, tmp_path / "puzzle_book_solution.pdf")

    puzzle_story = captured["puzzle_book.pdf"]
    solution_story = captured["puzzle_book_solution.pdf"]
    assert (
        sum(isinstance(flowable, PageBreak) for flowable in puzzle_story)
        == len(book.theme_puzzles) + 1
    )
    assert any(isinstance(flowable, Table) for flowable in puzzle_story)
    assert sum(isinstance(flowable, PageBreak) for flowable in solution_story) == 0
    assert sum(isinstance(flowable, Table) for flowable in solution_story) == 1


def test_summary_table_stores_stable_ids_not_localized_theme_labels() -> None:
    book = _book(theme_page_count=2, seed=9)

    for row in book.summary_table.rows:
        category = book.theme.category_by_id(row.theme_category_id)
        category_value_ids = {value.id for value in category.values}
        assert row.theme_category_instance_id
        assert set(row.value_ids_by_child) <= category_value_ids
        assert category.localized_label("en") != row.theme_category_id


def test_puzzle_book_generation_works_for_every_registered_theme() -> None:
    for index, theme_id in enumerate(
        (
            "tennis_training",
            "dance_studio",
            "beach_day",
            "athletics_training",
            "zoo_visit",
        )
    ):
        book = PuzzleBookGenerator(
            theme=theme_id, random_source=random.Random(100 + index), difficulty="easy"
        ).generate(theme_page_count=1)

        assert book.theme_id == theme_id
        assert len(book.theme_puzzles) == 1
        assert book.theme_puzzles[0].metadata is not None
        assert book.theme_puzzles[0].metadata.theme_id == theme_id
        assert book.theme_puzzles[0].metadata.theme_category_id in (
            PuzzleBookGenerator(theme=theme_id).available_category_ids
        )


def test_random_theme_uses_theme_registry() -> None:
    book = PuzzleBookGenerator(
        theme="random", random_source=random.Random(10), difficulty="easy"
    ).generate(theme_page_count=1)

    assert book.theme_id in DEFAULT_THEME_REGISTRY.supported_theme_ids()
    assert book.theme_puzzles[0].metadata is not None
    assert book.theme_puzzles[0].metadata.theme_id == book.theme_id
