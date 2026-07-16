import random

import pytest

from reportlab.platypus import PageBreak, Table

from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.engine.validator import Validator
from logical_puzzle_generator.generator.difficulty import (
    Difficulty,
    DifficultyContext,
    DifficultyPolicy,
)
from logical_puzzle_generator.generator.puzzle_book import PuzzleBook, PuzzleBookGenerator
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.model.solution import Solution
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY


def book_solution(children, values):
    from logical_puzzle_generator.model.position import Position

    positions = {}
    for index, child in enumerate(children, start=1):
        positions[child] = Position(index)
    for index, value in enumerate(values, start=1):
        positions[value] = Position(index)
    return Solution(Assignment(positions))


def _book(theme_page_count: int, seed: int = 0):
    return PuzzleBookGenerator(
        theme="tennis_training", random_source=random.Random(seed), difficulty="easy"
    ).generate(theme_page_count=theme_page_count)


def test_puzzle_book_reads_available_categories_from_selected_theme() -> None:
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    generator = PuzzleBookGenerator(theme="tennis_training", random_source=random.Random(0))

    assert generator.available_category_ids == tuple(category.id for category in theme.categories)
    assert "tournament_wins" in generator.available_category_ids


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
    assert book.position_puzzle.metadata is not None
    assert book.position_puzzle.metadata.theme_category_id is None
    assert book.position_puzzle.metadata.theme_category_instance_id is None
    assert book.position_puzzle.metadata.selected_theme_value_ids == ()


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
        theme_categories = [
            category for category in puzzle.categories if category.name != "Children"
        ]
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

    assert summary.child_names_by_position == tuple(child.name for child in book.stable_children)
    assert len(summary.rows) == len(book.theme_puzzles)
    assert all(row.theme_category_id != "Position" for row in summary.rows)
    assert [row.theme_category_instance_id for row in summary.rows] == [
        puzzle.metadata.theme_category_instance_id
        for puzzle in book.theme_puzzles
        if puzzle.metadata
    ]
    assert all(len(row.value_ids_by_position) == len(book.children) for row in summary.rows)


def test_puzzle_book_pdfs_use_expected_page_shapes(monkeypatch, tmp_path) -> None:
    book = _book(theme_page_count=2, seed=8)
    captured: dict[str, list[object]] = {}

    def capture_build(self, output_path, story, *, page_count=None):
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
        assert set(row.value_ids_by_position) <= category_value_ids
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


def test_puzzle_book_theme_pages_use_position_solution_as_fixed_child_context() -> None:
    book = _book(theme_page_count=4, seed=42)
    assert book.position_puzzle.solution is not None
    expected = dict(book.position_puzzle.solution.assignment.positions)

    for puzzle in book.theme_puzzles:
        assert puzzle.fixed_positions == expected
        assert puzzle.solution is not None
        for child, position in expected.items():
            assert puzzle.solution.assignment.position_of(child) == position


def test_puzzle_book_summary_uses_position_columns_and_name_row_source() -> None:
    book = _book(theme_page_count=2, seed=43)
    summary = book.summary_table

    assert summary.position_ids == (1, 2, 3, 4)
    assert summary.child_names_by_position == tuple(child.name for child in book.stable_children)
    assert len(summary.rows) == len(book.theme_puzzles)


def test_puzzle_book_lineup_field_modes_and_choices_for_text_and_numeric_pages(
    monkeypatch, tmp_path
) -> None:
    from logical_puzzle_generator.pdf.lineup import PlayerLineupRenderer

    class FixedCategories(PuzzleBookGenerator):
        def select_category_ids(self, theme_page_count: int) -> tuple[str, ...]:
            return ("training", "tournament_wins", "racket_count")[:theme_page_count]

    captured = {}

    def capture_build(self, output_path, story, *, page_count=None):
        captured[output_path.name] = story

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    book = FixedCategories(
        theme="tennis_training", random_source=random.Random(24), difficulty="easy"
    ).generate(theme_page_count=3)

    PdfGenerator(language="en").create_puzzle_book_pdf(book, tmp_path / "book.pdf")

    lineups = [
        flowable for flowable in captured["book.pdf"] if isinstance(flowable, PlayerLineupRenderer)
    ]
    assert len(lineups) == 4
    position_lineup, training_lineup, wins_lineup, rackets_lineup = lineups
    assert position_lineup.show_child_field is True
    assert position_lineup.show_theme_field is False
    assert position_lineup.child_field_heading == "Name"
    assert training_lineup.show_child_field is True
    assert training_lineup.show_theme_field is True
    assert training_lineup.child_field_heading == "Name"
    assert training_lineup.theme_field_heading == "Training"
    assert wins_lineup.show_child_field is True
    assert wins_lineup.show_theme_field is True
    assert wins_lineup.child_field_heading == "Name"
    assert wins_lineup.theme_field_heading == "Tournament Wins"
    assert rackets_lineup.show_child_field is True
    assert rackets_lineup.show_theme_field is True
    assert rackets_lineup.child_field_heading == "Name"
    assert rackets_lineup.theme_field_heading == "Rackets in Bag"

    tables = [flowable for flowable in captured["book.pdf"] if isinstance(flowable, Table)]
    table_texts = [str(table._cellvalues) for table in tables]
    assert sum("Available Names" in text for text in table_texts) == 1
    assert any("Training" in text for text in table_texts)
    assert any("Tournament" in text for text in table_texts)
    assert any("Rackets" in text for text in table_texts)


def test_solution_summary_uses_completed_subtitle_not_worksheet_instruction(
    monkeypatch, tmp_path
) -> None:
    from reportlab.platypus import Paragraph

    captured = {}

    def capture_build(self, output_path, story, *, page_count=None):
        captured[output_path.name] = story

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    book = _book(theme_page_count=1, seed=26)
    PdfGenerator(language="en").create_puzzle_book_solution_pdf(book, tmp_path / "solution.pdf")

    text = "\n".join(
        getattr(flowable, "text", "")
        for flowable in captured["solution.pdf"]
        if isinstance(flowable, Paragraph)
    )
    assert "Completed Summary" in text
    assert "First copy the names" not in text


def _category_instance_for(book, page):
    metadata = page.metadata
    category = book.theme.category_by_id(metadata.theme_category_id)
    selected_values = tuple(
        (
            category.parse_generated_numeric_value_id(
                value_id, instance_id=metadata.theme_category_instance_id
            )
            if category.is_numeric
            else category.value_by_id(value_id)
        )
        for value_id in metadata.selected_theme_value_ids
    )
    from logical_puzzle_generator.themes.registry import ThemeCategoryInstance

    return ThemeCategoryInstance(category, metadata.theme_category_instance_id, selected_values)


def _theme_items(page):
    return [item for item in page.logical_items if item.category_id != CHILDREN_CATEGORY_ID]


def _theme_direct_identities(page, book):
    return DifficultyPolicy().theme_direct_assignment_identities(
        page.constraints,
        fixed_child_positions=page.fixed_positions,
        theme_items=_theme_items(page),
        category_instance=_category_instance_for(book, page),
    )


def _theme_direct_count(page, book) -> int:
    return len(_theme_direct_identities(page, book))


def test_fixed_child_theme_page_difficulty_controls_direct_assignment_count() -> None:
    expected = {"easy": (1, 2), "medium": (2, 1), "hard": (3, 0)}
    for difficulty, (metadata_value, direct_count) in expected.items():
        book = PuzzleBookGenerator(
            theme="tennis_training", random_source=random.Random(72), difficulty=difficulty
        ).generate(theme_page_count=1)
        page = book.theme_puzzles[0]
        assert page.metadata is not None
        assert page.metadata.difficulty == metadata_value
        assert _theme_direct_count(page, book) == direct_count
        assert len(page.clues) == len(page.constraints)
        assert page.fixed_positions


def test_fixed_child_theme_page_direct_assignment_counts_across_categories_and_seeds() -> None:
    from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
    from logical_puzzle_generator.constraints.numeric import (
        NumericDifferenceConstraint,
        NumericMultipleConstraint,
    )
    from logical_puzzle_generator.engine.validator import Validator

    expected = {"easy": (1, 2), "medium": (2, 1), "hard": (3, 0)}

    for category_id in ("training", "tournament_wins", "racket_count"):
        for difficulty, (metadata_value, direct_count) in expected.items():
            for seed in (31, 32):

                class OneCategory(PuzzleBookGenerator):
                    def select_category_ids(self, theme_page_count: int) -> tuple[str, ...]:
                        return (category_id,)

                book = OneCategory(
                    theme="tennis_training",
                    random_source=random.Random(seed),
                    difficulty=difficulty,
                ).generate(theme_page_count=1)
                page = book.theme_puzzles[0]
                assert page.metadata is not None
                assert page.metadata.difficulty == metadata_value
                assert len(page.constraints) == len(page.clues) == 3
                assert _theme_direct_count(page, book) == direct_count
                assert page.fixed_positions == dict(
                    book.position_puzzle.solution.assignment.positions
                )
                assert all(
                    not (
                        isinstance(constraint, FixedPositionConstraint)
                        and constraint.item.category_id == CHILDREN_CATEGORY_ID
                    )
                    for constraint in page.constraints
                )
                assert page.solution is not None
                for child, position in page.fixed_positions.items():
                    assert page.solution.assignment.position_of(child) == position
                assert Validator().has_unique_solution(page)
                if category_id == "training":
                    from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
                    from logical_puzzle_generator.constraints.direct_left_of import (
                        DirectLeftOfConstraint,
                    )
                    from logical_puzzle_generator.constraints.direct_right_of import (
                        DirectRightOfConstraint,
                    )
                    from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
                    from logical_puzzle_generator.constraints.right_of import RightOfConstraint

                    assert any(
                        isinstance(
                            constraint,
                            (
                                DirectLeftOfConstraint,
                                DirectRightOfConstraint,
                                LeftOfConstraint,
                                RightOfConstraint,
                                AdjacentConstraint,
                            ),
                        )
                        for constraint in page.constraints
                    )
                assert len(_theme_direct_identities(page, book)) == sum(
                    1
                    for constraint in page.constraints
                    if DifficultyPolicy().is_theme_direct_assignment(constraint)
                )
                if category_id in {"tournament_wins", "racket_count"}:
                    relative_count = sum(
                        isinstance(
                            constraint, (NumericDifferenceConstraint, NumericMultipleConstraint)
                        )
                        for constraint in page.constraints
                    )
                    assert relative_count >= 1


def test_fixed_child_theme_selector_rejects_candidate_sets_with_too_few_direct_assignments() -> (
    None
):
    from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
    from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
    from logical_puzzle_generator.model.item import Item
    from logical_puzzle_generator.model.position import Position

    children = [Item("A"), Item("B"), Item("C"), Item("D")]
    values = [Item(f"v{i}", category_id="theme") for i in range(4)]
    generator = PuzzleGenerator(
        theme="tennis_training",
        difficulty="easy",
        fixed_child_positions={child: Position(index + 1) for index, child in enumerate(children)},
    )
    candidates = [
        SamePositionConstraint(children[0], values[0]),
        AdjacentConstraint(values[1], values[2]),
        AdjacentConstraint(values[2], values[3]),
    ]

    assert (
        generator._select_thematic_constraints(
            candidates,
            child_constraints=[],
            children=children,
            theme_items=values,
            solution=book_solution(children, values),
            difficulty=Difficulty.EASY,
        )
        is None
    )
    assert (
        generator._select_thematic_constraints(
            candidates[1:],
            child_constraints=[],
            children=children,
            theme_items=values,
            solution=book_solution(children, values),
            difficulty=Difficulty.MEDIUM,
        )
        is None
    )


def test_generation_failure_messages_are_context_specific(monkeypatch) -> None:
    from logical_puzzle_generator.model.item import Item
    from logical_puzzle_generator.model.position import Position

    children = [Item("A"), Item("B"), Item("C"), Item("D")]

    normal = PuzzleGenerator(difficulty="easy", max_attempts=1)
    monkeypatch.setattr(normal, "_generate_candidate", lambda *args, **kwargs: (None, "forced"))
    with pytest.raises(RuntimeError, match="child FixedPositionConstraint clues"):
        normal.generate(children)

    fixed = PuzzleGenerator(
        theme="tennis_training",
        difficulty="easy",
        max_attempts=1,
        fixed_child_positions={child: Position(index + 1) for index, child in enumerate(children)},
    )
    monkeypatch.setattr(fixed, "_generate_candidate", lambda *args, **kwargs: (None, "forced"))
    with pytest.raises(RuntimeError, match="direct Theme assignments"):
        fixed.generate(children)


def test_puzzle_book_page_number_context_for_zero_one_and_eight_theme_pages(
    monkeypatch, tmp_path
) -> None:
    captured: dict[str, int | None] = {}

    def capture_build(self, output_path, story, *, page_count=None):
        assert not hasattr(self, "_pending_page_count")
        captured[output_path.name] = page_count

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    for pages, expected_total in ((0, 2), (1, 3), (8, 10)):
        book = _book(theme_page_count=pages, seed=100 + pages)
        PdfGenerator(language="en").create_puzzle_book_pdf(book, tmp_path / f"book_{pages}.pdf")
        assert captured[f"book_{pages}.pdf"] == expected_total

    PdfGenerator(language="de").create_puzzle_book_solution_pdf(
        _book(theme_page_count=1, seed=109), tmp_path / "solution.pdf"
    )
    assert captured["solution.pdf"] == 1


def test_puzzle_book_position_page_uses_book_theme_header_and_explicit_instructions(
    monkeypatch, tmp_path
) -> None:
    from reportlab.platypus import Paragraph
    from logical_puzzle_generator.pdf.lineup import PlayerLineupRenderer

    captured = {}

    def capture_build(self, output_path, story, *, page_count=None):
        captured[output_path.name] = story

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    book = _book(theme_page_count=1, seed=117)

    PdfGenerator(language="en").create_puzzle_book_pdf(book, tmp_path / "book-en.pdf")
    PdfGenerator(language="de").create_puzzle_book_pdf(book, tmp_path / "book-de.pdf")

    english_text = "\n".join(
        flowable.text for flowable in captured["book-en.pdf"] if isinstance(flowable, Paragraph)
    )
    german_text = "\n".join(
        flowable.text for flowable in captured["book-de.pdf"] if isinstance(flowable, Paragraph)
    )

    assert "Theme: Tennis Training" in english_text
    assert "Question: Order of the Children" in english_text
    assert "Difficulty: Easy" in english_text
    assert "General" not in english_text
    assert "Write the correct name below each position" in english_text
    assert "First copy the names from Page 1 into the Name row" in english_text
    assert "Write the names" not in english_text

    assert "Thema: Tennistraining" in german_text
    assert "Frage: Reihenfolge der Kinder" in german_text
    assert "Schwierigkeit: Leicht" in german_text
    assert "Allgemein" not in german_text
    assert "Schreibe den richtigen Namen unter jede Position" in german_text
    assert "Übertrage zuerst die Namen von Seite 1" in german_text
    assert "Trage die Namen ein" not in german_text

    assert all(
        lineup.instruction == ""
        for lineup in captured["book-de.pdf"]
        if isinstance(lineup, PlayerLineupRenderer)
    )


def test_repeated_category_display_labels_number_pages_and_summary(monkeypatch, tmp_path) -> None:
    from reportlab.platypus import Paragraph, Table

    class RepeatedCategories(PuzzleBookGenerator):
        def select_category_ids(self, theme_page_count: int) -> tuple[str, ...]:
            return ("playing_style", "playing_style", "racket_count")[:theme_page_count]

    captured = {}

    def capture_build(self, output_path, story, *, page_count=None):
        captured[output_path.name] = story

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    book = RepeatedCategories(
        theme="tennis_training", random_source=random.Random(44), difficulty="easy"
    ).generate(theme_page_count=3)
    PdfGenerator(language="de").create_puzzle_book_pdf(book, tmp_path / "book.pdf")

    paragraphs = [
        flowable.text for flowable in captured["book.pdf"] if isinstance(flowable, Paragraph)
    ]
    assert any("Frage: Spielstil 1" in text for text in paragraphs)
    assert any("Frage: Spielstil 2" in text for text in paragraphs)
    assert any("Frage: Schläger in der Tasche" in text for text in paragraphs)

    summary = [flowable for flowable in captured["book.pdf"] if isinstance(flowable, Table)][-1]
    row_labels = [row[0] for row in summary._cellvalues[2:]]
    assert row_labels == ["Spielstil 1", "Spielstil 2", "Schläger in der Tasche"]


def _pdf_page_count(path) -> int:
    text = path.read_bytes().decode("latin-1")
    return text.count("/Type /Page") - text.count("/Type /Pages")


def test_puzzle_book_physical_page_count_matches_declared_footer(tmp_path) -> None:
    book = _book(theme_page_count=2, seed=131)
    puzzle_path = tmp_path / "book.pdf"
    solution_path = tmp_path / "solution.pdf"
    pdf = PdfGenerator(language="en")

    pdf.create_puzzle_book_pdf(book, puzzle_path)
    pdf.create_puzzle_book_solution_pdf(book, solution_path)

    puzzle_text = puzzle_path.read_bytes().decode("latin-1")
    solution_text = solution_path.read_bytes().decode("latin-1")
    assert _pdf_page_count(puzzle_path) == 4
    assert _pdf_page_count(solution_path) == 1
    assert "Page 1 / 4" in puzzle_text
    assert "Page 4 / 4" in puzzle_text
    assert "Page 1 / 1" in solution_text


def test_failed_puzzle_book_build_leaves_no_page_count_state(monkeypatch, tmp_path) -> None:
    def failing_build(self, output_path, story, *, page_count=None):
        assert page_count == 3
        raise OSError("forced build failure")

    monkeypatch.setattr(PdfGenerator, "_build", failing_build)
    generator = PdfGenerator(language="en")
    with pytest.raises(OSError, match="forced build failure"):
        generator.create_puzzle_book_pdf(_book(theme_page_count=1, seed=141), tmp_path / "book.pdf")
    assert not hasattr(generator, "_pending_page_count")


def _difficulty_for_metadata_value(value: int) -> Difficulty:
    for difficulty in Difficulty:
        if difficulty.metadata_value == value:
            return difficulty
    raise AssertionError(f"Unexpected metadata difficulty: {value}")


def _category_instance_from_metadata(book, metadata):
    category = book.theme.category_by_id(metadata.theme_category_id)
    if category.is_numeric:
        selected_values = tuple(
            category.parse_generated_numeric_value_id(
                value_id, instance_id=metadata.theme_category_instance_id
            )
            for value_id in metadata.selected_theme_value_ids
        )
    else:
        selected_values = tuple(
            category.value_by_id(value_id) for value_id in metadata.selected_theme_value_ids
        )
    return __import__(
        "logical_puzzle_generator.themes.registry", fromlist=["ThemeCategoryInstance"]
    ).ThemeCategoryInstance(category, metadata.theme_category_instance_id, selected_values)


def test_mixed_puzzle_book_stores_concrete_page_metadata_and_matches_plan() -> None:
    plan = PuzzleBookGenerator(
        theme="tennis_training", seed=42, difficulty="mixed"
    )._resolve_difficulty_plan(3)
    book = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="mixed").generate(
        theme_page_count=3
    )

    assert book.position_puzzle.metadata is not None
    assert book.position_puzzle.metadata.difficulty == plan.position_difficulty.metadata_value
    assert [p.metadata.difficulty for p in book.theme_puzzles if p.metadata] == [
        difficulty.metadata_value for difficulty in plan.theme_page_difficulties
    ]
    assert all(p.metadata and p.metadata.difficulty in {1, 2, 3} for p in book.pages)
    assert all(len(p.clues) == 3 for p in book.theme_puzzles)


def test_mixed_puzzle_book_composition_matches_each_page_difficulty() -> None:
    book = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="mixed").generate(
        theme_page_count=2
    )
    policy = DifficultyPolicy()
    validator = Validator()
    expected_positions = dict(book.position_puzzle.solution.assignment.positions)

    position_difficulty = _difficulty_for_metadata_value(book.position_puzzle.metadata.difficulty)
    assert policy.direct_assignment_count(
        book.position_puzzle, context=DifficultyContext.POSITION_PAGE
    ) == policy.required_fixed_position_count(position_difficulty)

    for puzzle in book.theme_puzzles:
        assert puzzle.metadata is not None
        assert puzzle.solution is not None
        assert puzzle.fixed_positions == expected_positions
        assert len(puzzle.constraints) == 3
        assert len(puzzle.clues) == 3
        assert validator.has_unique_solution(puzzle)
        difficulty = _difficulty_for_metadata_value(puzzle.metadata.difficulty)
        theme_items = [
            item
            for category in puzzle.categories
            for item in category.items
            if item.category_id != CHILDREN_CATEGORY_ID
        ]
        category_instance = _category_instance_from_metadata(book, puzzle.metadata)
        direct_count = policy.direct_assignment_count(
            puzzle,
            context=DifficultyContext.FIXED_CHILD_THEME_PAGE,
            fixed_child_positions=puzzle.fixed_positions,
            theme_items=theme_items,
            category_instance=category_instance,
        )
        assert direct_count == policy.required_direct_assignment_count(difficulty)
        assert len(puzzle.constraints) - direct_count == 3 - direct_count


def test_mixed_puzzle_book_child_mapping_is_stable() -> None:
    book = PuzzleBookGenerator(theme="tennis_training", seed=45, difficulty="mixed").generate(
        theme_page_count=3
    )
    expected = dict(book.position_puzzle.solution.assignment.positions)

    for puzzle in book.theme_puzzles:
        assert puzzle.fixed_positions == expected


def test_mixed_retry_keeps_page_difficulty_plan_and_later_page_streams(monkeypatch) -> None:
    baseline = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="mixed").generate(
        theme_page_count=3
    )
    original = PuzzleGenerator._generate_candidate
    fixed_child_attempts = 0
    observed: list[Difficulty] = []

    def fail_first_fixed_child_attempt(self, source, items, difficulty, *args, **kwargs):
        nonlocal fixed_child_attempts
        if self._fixed_child_positions is not None:
            observed.append(difficulty)
            fixed_child_attempts += 1
            if fixed_child_attempts == 1:
                return None, "forced retry"
        return original(self, source, items, difficulty, *args, **kwargs)

    monkeypatch.setattr(PuzzleGenerator, "_generate_candidate", fail_first_fixed_child_attempt)
    plan = PuzzleBookGenerator(
        theme="tennis_training", seed=42, difficulty="mixed"
    )._resolve_difficulty_plan(3)

    retried = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="mixed").generate(
        theme_page_count=3
    )

    assert [p.metadata.theme_category_id for p in retried.theme_puzzles if p.metadata] == [
        p.metadata.theme_category_id for p in baseline.theme_puzzles if p.metadata
    ]
    assert [p.metadata.difficulty for p in retried.theme_puzzles if p.metadata] == [
        difficulty.metadata_value for difficulty in plan.theme_page_difficulties
    ]
    assert observed[0] is plan.theme_page_difficulties[0]
    assert observed[1] is plan.theme_page_difficulties[0]
    assert _deterministic_book_signature(
        PuzzleBook(
            theme=baseline.theme,
            children=baseline.children,
            position_puzzle=baseline.position_puzzle,
            theme_puzzles=baseline.theme_puzzles[1:],
        )
    ) == _deterministic_book_signature(
        PuzzleBook(
            theme=retried.theme,
            children=retried.children,
            position_puzzle=retried.position_puzzle,
            theme_puzzles=retried.theme_puzzles[1:],
        )
    )


def test_mixed_puzzle_book_pdf_headers_use_concrete_localized_difficulties(
    monkeypatch, tmp_path
) -> None:
    from reportlab.platypus import Paragraph

    captured = {}

    def capture_build(self, output_path, story, *, page_count=None):
        captured[output_path.name] = story

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    book = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="mixed").generate(
        theme_page_count=2
    )

    PdfGenerator(language="en").create_puzzle_book_pdf(book, tmp_path / "book-en.pdf")
    PdfGenerator(language="de").create_puzzle_book_pdf(book, tmp_path / "book-de.pdf")

    english = "\n".join(
        flowable.text for flowable in captured["book-en.pdf"] if isinstance(flowable, Paragraph)
    )
    german = "\n".join(
        flowable.text for flowable in captured["book-de.pdf"] if isinstance(flowable, Paragraph)
    )
    assert "Difficulty: Easy" in english
    assert "Difficulty: Medium" in english
    assert "Difficulty: Hard" in english
    assert "Difficulty: Mixed" not in english
    assert "Schwierigkeit: Leicht" in german
    assert "Schwierigkeit: Mittel" in german
    assert "Schwierigkeit: Schwer" in german
    assert "Schwierigkeit: Gemischt" not in german


def test_mixed_puzzle_book_fourteen_theme_pages_keep_physical_page_count(tmp_path) -> None:
    book = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="mixed").generate(
        theme_page_count=14
    )
    puzzle_path = tmp_path / "mixed_book.pdf"
    solution_path = tmp_path / "mixed_solution.pdf"

    PdfGenerator(language="de").create_puzzle_book_pdf(book, puzzle_path)
    PdfGenerator(language="de").create_puzzle_book_solution_pdf(book, solution_path)

    puzzle_text = puzzle_path.read_bytes().decode("latin-1")
    solution_text = solution_path.read_bytes().decode("latin-1")
    assert _pdf_page_count(puzzle_path) == 16
    assert _pdf_page_count(solution_path) == 1
    assert "Seite 1 / 16" in puzzle_text
    assert "Seite 16 / 16" in puzzle_text
    assert "Seite 1 / 1" in solution_text
    assert "Schwierigkeit: Gemischt" not in puzzle_text


def test_puzzle_book_seed_and_random_source_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="Specify either seed or random_source"):
        PuzzleBookGenerator(theme="tennis_training", seed=1, random_source=random.Random(1))


def test_difficulty_planning_does_not_shift_category_selection_stream() -> None:
    uniform = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="easy")
    mixed = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="mixed")

    uniform._resolve_difficulty_plan(5)
    mixed._resolve_difficulty_plan(5)

    assert uniform.select_category_ids(5) == mixed.select_category_ids(5)


def _deterministic_book_signature(book):
    def item_key(item):
        return (item.category_id, item.name)

    def assignment_signature(puzzle):
        return tuple(
            sorted(
                (item_key(item), position.index)
                for item, position in puzzle.solution.assignment.positions.items()
            )
        )

    return (
        book.theme_id,
        tuple(child.name for child in book.children),
        assignment_signature(book.position_puzzle),
        tuple(p.metadata.difficulty for p in book.pages if p.metadata),
        tuple(p.metadata.theme_category_id for p in book.theme_puzzles if p.metadata),
        tuple(p.metadata.theme_category_instance_id for p in book.theme_puzzles if p.metadata),
        tuple(p.metadata.selected_theme_value_ids for p in book.theme_puzzles if p.metadata),
        tuple(
            tuple(
                (type(constraint).__name__, constraint.description) for constraint in p.constraints
            )
            for p in book.pages
        ),
        tuple(assignment_signature(p) for p in book.pages),
    )


def test_seeded_generator_repeated_generate_calls_are_idempotent() -> None:
    generator = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="mixed")

    first = generator.generate(theme_page_count=3)
    second = generator.generate(theme_page_count=3)

    assert _deterministic_book_signature(first) == _deterministic_book_signature(second)


def test_random_source_generators_are_internally_deterministic() -> None:
    first = PuzzleBookGenerator(
        theme="tennis_training", random_source=random.Random(42), difficulty="mixed"
    ).generate(theme_page_count=3)
    second = PuzzleBookGenerator(
        theme="tennis_training", random_source=random.Random(42), difficulty="mixed"
    ).generate(theme_page_count=3)

    assert _deterministic_book_signature(first) == _deterministic_book_signature(second)


def test_random_source_consumes_exactly_one_64_bit_base_seed() -> None:
    class CountingRandom(random.Random):
        def __init__(self, seed: int) -> None:
            super().__init__(seed)
            self.getrandbits_calls: list[int] = []

        def getrandbits(self, k: int) -> int:
            self.getrandbits_calls.append(k)
            return super().getrandbits(k)

    source = CountingRandom(42)
    generator = PuzzleBookGenerator(
        theme="tennis_training",
        random_source=source,
        difficulty="mixed",
    )

    assert source.getrandbits_calls == [64]
    generator.generate(theme_page_count=3)
    assert source.getrandbits_calls == [64]


def test_random_theme_selection_is_seed_deterministic() -> None:
    first = PuzzleBookGenerator(theme="random", seed=42, difficulty="easy").generate(
        theme_page_count=1
    )
    second = PuzzleBookGenerator(theme="random", seed=42, difficulty="mixed").generate(
        theme_page_count=1
    )

    assert first.theme_id == second.theme_id


def test_category_isolation_between_uniform_and_mixed_books() -> None:
    uniform = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="easy").generate(
        theme_page_count=5
    )
    mixed = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="mixed").generate(
        theme_page_count=5
    )

    assert uniform.theme_id == mixed.theme_id
    assert tuple(child.name for child in uniform.children) == tuple(
        child.name for child in mixed.children
    )
    assert [p.metadata.theme_category_id for p in uniform.theme_puzzles if p.metadata] == [
        p.metadata.theme_category_id for p in mixed.theme_puzzles if p.metadata
    ]


def test_pdf_rendering_randomness_does_not_mutate_book_domain(tmp_path) -> None:
    from logical_puzzle_generator.pdf.generator import PdfGenerator
    from logical_puzzle_generator.random_streams import derived_random

    book = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="mixed").generate(
        theme_page_count=2
    )
    before = _deterministic_book_signature(book)

    PdfGenerator(
        language="en", random_source=derived_random(1, "puzzle_book.pdf")
    ).create_puzzle_book_pdf(book, tmp_path / "first.pdf")
    PdfGenerator(
        language="en", random_source=derived_random(2, "puzzle_book.pdf")
    ).create_puzzle_book_pdf(book, tmp_path / "second.pdf")

    assert _deterministic_book_signature(book) == before
