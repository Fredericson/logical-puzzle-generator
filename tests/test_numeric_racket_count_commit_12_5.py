from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.clue_text_renderer import ClueTextRenderer
from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.constraints.numeric import (
    ExactNumericValueConstraint,
    NumericDifferenceConstraint,
    NumericMultipleConstraint,
)
from logical_puzzle_generator.engine.assignment_iterator import AssignmentIterator
from logical_puzzle_generator.engine.solver import Solver
from logical_puzzle_generator.generator.puzzle_book import PuzzleBookGenerator
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.themes.children import select_child_items
from logical_puzzle_generator.themes.presentation import ItemPresentationResolver
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY


def _racket_instance(seed: int = 1, instance_index: int = 1):
    return DEFAULT_THEME_REGISTRY.resolve("tennis_training").create_category_instance(
        category_id="racket_count", random_source=random.Random(seed), instance_index=instance_index
    )


def test_racket_count_registration_is_tennis_only_and_complete() -> None:
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category = tennis.category_by_id("racket_count")
    assert category.localized_label("en") == "Rackets in Bag"
    assert category.localized_label("de") == "Schläger in der Tasche"
    assert category.is_numeric
    assert category.values == ()
    assert (category.numeric_minimum, category.numeric_maximum) == (1, 8)
    assert category.wording.numeric_exact is not None
    assert category.wording.numeric_more is not None
    assert category.wording.numeric_fewer is not None
    assert category.wording.numeric_twice is not None
    assert category.wording.unit_singular is not None
    assert category.wording.unit_plural is not None
    for theme_id in ("dance_studio", "beach_day", "athletics_training", "zoo_visit"):
        with pytest.raises(ValueError):
            DEFAULT_THEME_REGISTRY.resolve(theme_id).category_by_id("racket_count")


def test_generated_racket_values_are_small_distinct_generic_ids_and_roundtrip() -> None:
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category = tennis.category_by_id("racket_count")
    seen_sets: set[tuple[int, ...]] = set()
    for seed in range(1, 8):
        instance = tennis.create_category_instance(
            category_id="racket_count", random_source=random.Random(seed), instance_index=seed
        )
        raw_numbers = [value.numeric_value for value in instance.selected_values]
        assert len(raw_numbers) == 4
        assert all(isinstance(number, int) for number in raw_numbers)
        numbers = [number for number in raw_numbers if isinstance(number, int)]
        assert len(set(numbers)) == 4
        assert all(1 <= number <= 8 for number in numbers)
        assert 0 not in numbers
        assert any(a == 2 * b for a in numbers for b in numbers if a != b)
        seen_sets.add(tuple(sorted(numbers)))
        for value in instance.selected_values:
            assert value.id.startswith(f"{instance.instance_id}_value_")
            assert "wins" not in value.id
            assert "rackets_" not in value.id
            rebuilt = category.parse_generated_numeric_value_id(
                value.id, instance_id=instance.instance_id
            )
            assert rebuilt == value
            assert instance.value_by_id(rebuilt.id) == rebuilt
    assert len(seen_sets) > 1


def test_racket_count_reuses_existing_numeric_constraints() -> None:
    emma, mia = Item("Emma"), Item("Mia")
    values = {"racket_count_1_value_2": 2, "racket_count_1_value_4": 4}
    items = [
        emma,
        mia,
        Item("racket_count_1_value_2", "racket_count"),
        Item("racket_count_1_value_4", "racket_count"),
    ]
    assignment = next(AssignmentIterator().iterate(items))
    exact = ExactNumericValueConstraint(emma, 2, category_id="racket_count", values_by_id=values)
    diff = NumericDifferenceConstraint(
        mia, emma, 2, category_id="racket_count", values_by_id=values
    )
    multiple = NumericMultipleConstraint(
        mia, emma, 2, category_id="racket_count", values_by_id=values
    )
    assert exact.category_id == diff.category_id == multiple.category_id == "racket_count"
    assert exact.matches(assignment)
    assert diff.matches(assignment)
    assert multiple.matches(assignment)


@pytest.mark.parametrize(("difficulty", "anchors"), [("easy", 2), ("medium", 1), ("hard", 0)])
def test_racket_count_puzzles_are_unique_and_keep_fixed_position_difficulty(
    difficulty: str, anchors: int
) -> None:
    for seed in range(1, 4):
        puzzle = PuzzleGenerator(
            random_source=random.Random(seed),
            difficulty=difficulty,
            theme="tennis_training",
            category="racket_count",
            max_attempts=100,
        ).generate(select_child_items(random.Random(7)))
        result = Solver().solve(puzzle, stop_after=2)
        assert result.has_unique_solution
        assert result.statistics.assignments_checked <= 24 * 24
        assert len(puzzle.clues) == len(puzzle.constraints)
        assert any(
            isinstance(constraint, (NumericDifferenceConstraint, NumericMultipleConstraint))
            for constraint in puzzle.constraints
        )
        assert (
            sum(
                isinstance(c, FixedPositionConstraint) and c.item.category_id == "children"
                for c in puzzle.constraints
            )
            == anchors
        )


def test_racket_count_english_rendering_singular_plural_and_seeded_more_fewer() -> None:
    resolver = ItemPresentationResolver(
        DEFAULT_THEME_REGISTRY.resolve("tennis_training"), _racket_instance()
    )
    emma, mia, aurelia = Item("Emma"), Item("Mia"), Item("Aurelia")
    values = {"racket_count_1_value_1": 1, "racket_count_1_value_2": 2, "racket_count_1_value_4": 4}

    def render(constraint, seed=1):
        return ClueTextRenderer(
            "en", presentation_resolver=resolver, random_source=random.Random(seed)
        ).render_clue(Clue(ClueType.EXACT_NUMERIC_VALUE, "", constraint))

    assert (
        render(
            ExactNumericValueConstraint(emma, 1, category_id="racket_count", values_by_id=values)
        )
        == "Emma has 1 racket in her bag."
    )
    assert (
        render(
            ExactNumericValueConstraint(emma, 4, category_id="racket_count", values_by_id=values)
        )
        == "Emma has 4 rackets in her bag."
    )
    one = NumericDifferenceConstraint(mia, emma, 1, category_id="racket_count", values_by_id=values)
    two = NumericDifferenceConstraint(mia, emma, 2, category_id="racket_count", values_by_id=values)
    assert render(one, seed=0) == "Emma has 1 fewer racket in her bag than Mia."
    assert render(two, seed=0) == "Emma has 2 fewer rackets in her bag than Mia."
    assert render(one, seed=1) == "Mia has 1 more racket in her bag than Emma."
    assert render(two, seed=1) == "Mia has 2 more rackets in her bag than Emma."
    assert (
        render(
            NumericMultipleConstraint(
                aurelia, mia, 2, category_id="racket_count", values_by_id=values
            )
        )
        == "Aurelia has twice as many rackets in her bag as Mia."
    )


def test_racket_count_german_rendering_is_natural_swiss_and_hides_ids() -> None:
    resolver = ItemPresentationResolver(
        DEFAULT_THEME_REGISTRY.resolve("tennis_training"), _racket_instance(), "de"
    )
    emma, mia, aurelia = Item("Emma"), Item("Mia"), Item("Aurelia")
    values = {"racket_count_1_value_1": 1, "racket_count_1_value_2": 2, "racket_count_1_value_4": 4}

    def renderer(constraint, seed=1):
        return ClueTextRenderer(
            "de", presentation_resolver=resolver, random_source=random.Random(seed)
        ).render_clue(Clue(ClueType.EXACT_NUMERIC_VALUE, "", constraint))

    rendered = [
        renderer(
            ExactNumericValueConstraint(emma, 1, category_id="racket_count", values_by_id=values)
        ),
        renderer(
            ExactNumericValueConstraint(emma, 4, category_id="racket_count", values_by_id=values)
        ),
        renderer(
            NumericDifferenceConstraint(
                mia, emma, 1, category_id="racket_count", values_by_id=values
            ),
            0,
        ),
        renderer(
            NumericDifferenceConstraint(
                mia, emma, 2, category_id="racket_count", values_by_id=values
            ),
            1,
        ),
        renderer(
            NumericMultipleConstraint(
                aurelia, mia, 2, category_id="racket_count", values_by_id=values
            )
        ),
    ]
    assert "Emma hat 1 Schläger in ihrer Tasche." in rendered
    assert "Emma hat 4 Schläger in ihrer Tasche." in rendered
    assert any(
        "weniger in ihrer Tasche" in text or "mehr in ihrer Tasche" in text for text in rendered
    )
    assert "Aurelia hat doppelt so viele Schläger in ihrer Tasche wie Mia." in rendered
    assert all("Schläger" in text and "Tasche" in text and "ß" not in text for text in rendered)
    assert all("racket_count_" not in text for text in rendered)


def test_racket_count_relative_position_wording_keeps_bag_context() -> None:
    instance = _racket_instance()
    resolver_en = ItemPresentationResolver(
        DEFAULT_THEME_REGISTRY.resolve("tennis_training"), instance, "en"
    )
    resolver_de = ItemPresentationResolver(
        DEFAULT_THEME_REGISTRY.resolve("tennis_training"), instance, "de"
    )
    seven_value, eight_value = instance.selected_values[:2]
    seven = Item(seven_value.id, category_id="racket_count")
    eight = Item(eight_value.id, category_id="racket_count")

    cases = [
        LeftOfConstraint(seven, eight),
        DirectLeftOfConstraint(seven, eight),
        AdjacentConstraint(seven, eight),
        RightOfConstraint(eight, seven),
    ]
    for constraint in cases:
        clue = Clue(ClueType.LEFT_OF, "", constraint)
        en = ClueTextRenderer("en", presentation_resolver=resolver_en).render_clue(clue)
        de = ClueTextRenderer("de", presentation_resolver=resolver_de).render_clue(clue)
        assert "rackets in her bag" in en
        assert "Schlägern in der Tasche" in de
        assert "racket_count_" not in en + de
        assert "ß" not in de


def test_racket_count_position_anchor_rendering_is_data_driven() -> None:
    resolver_en = ItemPresentationResolver(
        DEFAULT_THEME_REGISTRY.resolve("tennis_training"), _racket_instance(), "en"
    )
    resolver_de = ItemPresentationResolver(
        DEFAULT_THEME_REGISTRY.resolve("tennis_training"), _racket_instance(), "de"
    )
    clue = Clue(
        ClueType.FIXED_POSITION,
        "",
        FixedPositionConstraint(Item("racket_count_1_value_4", "racket_count"), Position(2)),
    )

    assert (
        ClueTextRenderer("en", presentation_resolver=resolver_en).render_clue(clue)
        == "The child in Position 2 has 4 rackets in her bag."
    )
    german = ClueTextRenderer("de", presentation_resolver=resolver_de).render_clue(clue)
    assert german == "Das Kind auf Position 2 hat 4 Schläger in ihrer Tasche."
    assert "racket_count" not in german and "ß" not in german


def test_puzzle_book_repeated_racket_count_rows_are_instance_scoped_and_summarized() -> None:
    class RepeatedRacketBookGenerator(PuzzleBookGenerator):
        def select_category_ids(self, theme_page_count: int) -> tuple[str, ...]:
            return ("racket_count", "racket_count")

    book = RepeatedRacketBookGenerator(
        random_source=random.Random(6), difficulty="easy", theme="tennis_training"
    ).generate(theme_page_count=2)
    assert len(book.theme_puzzles) == 2
    assert book.summary_table.child_names_by_position == tuple(
        child.name for child in book.stable_children
    )
    rows = book.summary_table.rows
    assert [row.theme_category_id for row in rows] == ["racket_count", "racket_count"]
    assert rows[0].theme_category_instance_id != rows[1].theme_category_instance_id
    for row in rows:
        assert len(row.value_ids_by_position) == 4
        assert all(
            value_id.startswith(f"{row.theme_category_instance_id}_value_")
            for value_id in row.value_ids_by_position
        )
        assert all(
            book.theme.category_by_id("racket_count")
            .parse_generated_numeric_value_id(value_id, instance_id=row.theme_category_instance_id)
            .display("en")
            .isdigit()
            for value_id in row.value_ids_by_position
        )


def test_racket_count_pdf_story_has_headings_choices_summary_and_no_ids(
    monkeypatch, tmp_path
) -> None:
    from reportlab.platypus import Paragraph, Table

    class RepeatedRacketBookGenerator(PuzzleBookGenerator):
        def select_category_ids(self, theme_page_count: int) -> tuple[str, ...]:
            return ("racket_count",)

    captured = {}

    def capture_build(self, output_path, story, *, page_count=None):
        captured[output_path.name] = story

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    book = RepeatedRacketBookGenerator(
        random_source=random.Random(8), difficulty="easy", theme="tennis_training"
    ).generate(theme_page_count=1)
    PdfGenerator(language="en").create_puzzle_book_pdf(book, tmp_path / "puzzle_book.pdf")
    PdfGenerator(language="de").create_puzzle_book_solution_pdf(book, tmp_path / "solution.pdf")
    puzzle_text = "\n".join(
        getattr(flowable, "text", "")
        for flowable in captured["puzzle_book.pdf"]
        if isinstance(flowable, Paragraph)
    )
    table_text = "\n".join(
        str(cell)
        for flowable in captured["puzzle_book.pdf"]
        if isinstance(flowable, Table)
        for row in flowable._cellvalues
        for cell in row
    )
    assert "Rackets in Bag" in table_text
    assert "racket_count_" not in puzzle_text + table_text
    unsolved_table = [f for f in captured["puzzle_book.pdf"] if isinstance(f, Table)][-1]
    assert all(cell == "" for row in unsolved_table._cellvalues[1:] for cell in row[1:])
    solution_story = captured["solution.pdf"]
    solved_table = [f for f in solution_story if isinstance(f, Table)][-1]
    assert len([f for f in solution_story if isinstance(f, Table)]) == 1
    assert "Schläger in der Tasche" in [row[0] for row in solved_table._cellvalues[1:]]
    solved_cells = [str(cell) for row in solved_table._cellvalues[2:] for cell in row[1:]]
    assert all(cell.isdigit() for cell in solved_cells)
    assert all(not cell.startswith("racket_count_") for cell in solved_cells)


def test_racket_count_single_puzzle_cli_en_de_and_invalid_theme(tmp_path, monkeypatch) -> None:
    from logical_puzzle_generator.create_puzzle import main

    monkeypatch.chdir(tmp_path)
    en = main(
        [
            "--number",
            "41",
            "--theme",
            "tennis_training",
            "--category",
            "racket_count",
            "--difficulty",
            "easy",
            "--language",
            "en",
        ]
    )
    de = main(
        [
            "--number",
            "42",
            "--theme",
            "tennis_training",
            "--category",
            "racket_count",
            "--difficulty",
            "easy",
            "--language",
            "de",
        ]
    )
    assert en.metadata is not None and en.metadata.theme_category_id == "racket_count"
    assert de.metadata is not None and de.metadata.theme_category_id == "racket_count"
    assert (tmp_path / "output" / "puzzle_41.pdf").exists()
    assert (tmp_path / "output" / "puzzle_41_solution.pdf").exists()
    assert (tmp_path / "output" / "puzzle_42.pdf").exists()
    assert (tmp_path / "output" / "puzzle_42_solution.pdf").exists()
    with pytest.raises(ValueError, match="has no category 'racket_count'"):
        main(
            [
                "--number",
                "43",
                "--theme",
                "dance_studio",
                "--category",
                "racket_count",
                "--difficulty",
                "easy",
                "--language",
                "en",
            ]
        )
