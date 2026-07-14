from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.clue_text_renderer import ClueTextRenderer
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.numeric import (
    ExactNumericValueConstraint,
    NumericDifferenceConstraint,
    NumericMultipleConstraint,
)
from logical_puzzle_generator.engine.assignment_iterator import AssignmentIterator
from logical_puzzle_generator.engine.solver import Solver
from logical_puzzle_generator.generator import Difficulty
from logical_puzzle_generator.generator.puzzle_book import PuzzleBookGenerator
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.themes.children import select_child_items
from logical_puzzle_generator.themes.presentation import ItemPresentationResolver
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY


def test_tournament_wins_registration_and_instances() -> None:
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category = tennis.category_by_id("tournament_wins")
    assert category.is_numeric
    for theme_id in ("dance_studio", "beach_day", "athletics_training", "zoo_visit"):
        with pytest.raises(ValueError):
            DEFAULT_THEME_REGISTRY.resolve(theme_id).category_by_id("tournament_wins")

    first = tennis.create_category_instance(
        category_id="tournament_wins", random_source=random.Random(1), instance_index=1
    )
    second = tennis.create_category_instance(
        category_id="tournament_wins", random_source=random.Random(2), instance_index=2
    )
    assert first.instance_id != second.instance_id
    assert len(first.selected_values) == 4
    numbers = [value.numeric_value for value in first.selected_values]
    assert len(set(numbers)) == 4
    assert all(isinstance(value, int) and value >= 0 for value in numbers)
    assert [
        first.value_by_id(value_id).numeric_value for value_id in first.selected_value_ids
    ] == numbers


def test_arithmetic_constraints_match_and_reject() -> None:
    children = [Item("Emma"), Item("Mia")]
    values = {"sample_1_value_5": 5, "sample_1_value_10": 10}
    items = [
        *children,
        Item("sample_1_value_5", category_id="tournament_wins"),
        Item("sample_1_value_10", category_id="tournament_wins"),
    ]
    assignment = next(AssignmentIterator().iterate(items))
    assert ExactNumericValueConstraint(
        children[0], 5, category_id="tournament_wins", values_by_id=values
    ).matches(assignment)
    assert not ExactNumericValueConstraint(
        children[0], 10, category_id="tournament_wins", values_by_id=values
    ).matches(assignment)
    assert NumericDifferenceConstraint(
        children[1], children[0], 5, category_id="tournament_wins", values_by_id=values
    ).matches(assignment)
    assert NumericMultipleConstraint(
        children[1], children[0], 2, category_id="tournament_wins", values_by_id=values
    ).matches(assignment)
    with pytest.raises(ValueError):
        NumericMultipleConstraint(
            children[1], children[0], 3, category_id="tournament_wins", values_by_id=values
        )


def test_generated_tournament_wins_puzzle_is_unique_and_category_aware() -> None:
    puzzle = PuzzleGenerator(
        random_source=random.Random(12),
        difficulty=Difficulty.EASY,
        theme="tennis_training",
        category="tournament_wins",
    ).generate(select_child_items(random.Random(7)))
    assert puzzle.metadata is not None
    assert puzzle.metadata.theme_category_id == "tournament_wins"
    assert len(puzzle.metadata.selected_theme_value_ids) == 4
    assert any(
        isinstance(
            constraint,
            (ExactNumericValueConstraint, NumericDifferenceConstraint, NumericMultipleConstraint),
        )
        for constraint in puzzle.constraints
    )
    result = Solver().solve(puzzle, stop_after=3)
    assert result.has_unique_solution
    assert result.statistics.assignments_checked <= 24 * 24


def test_arithmetic_clue_rendering_en_and_de() -> None:
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    instance = tennis.create_category_instance(
        category_id="tournament_wins", random_source=random.Random(3), instance_index=1
    )
    resolver = ItemPresentationResolver(tennis, instance)
    values = {
        "tournament_wins_1_value_1": 1,
        "tournament_wins_1_value_5": 5,
        "tournament_wins_1_value_9": 9,
        "tournament_wins_1_value_10": 10,
    }
    emma, mia = Item("Emma"), Item("Mia")
    exact = Clue(
        ClueType.EXACT_NUMERIC_VALUE,
        "",
        ExactNumericValueConstraint(emma, 1, category_id="tournament_wins", values_by_id=values),
    )
    diff = Clue(
        ClueType.NUMERIC_DIFFERENCE,
        "",
        NumericDifferenceConstraint(
            mia, emma, 4, category_id="tournament_wins", values_by_id=values
        ),
    )
    twice = Clue(
        ClueType.NUMERIC_MULTIPLE,
        "",
        NumericMultipleConstraint(mia, emma, 2, category_id="tournament_wins", values_by_id=values),
    )
    en = ClueTextRenderer("en", presentation_resolver=resolver, random_source=random.Random(1))
    de = ClueTextRenderer("de", presentation_resolver=resolver, random_source=random.Random(1))
    assert en.render_clue(exact) == "Emma won 1 tournament."
    assert "4 tournaments" in en.render_clue(diff)
    assert en.render_clue(twice) == "Mia won twice as many tournaments as Emma."
    assert de.render_clue(exact) == "Emma gewann 1 Turnier."
    german = de.render_clue(diff) + de.render_clue(twice)
    assert "Turniere" in german
    assert "ß" not in german


def test_puzzle_book_repeated_tournament_wins_rows() -> None:
    class RepeatedTournamentWinsBookGenerator(PuzzleBookGenerator):
        def select_category_ids(self, theme_page_count: int) -> tuple[str, ...]:
            return ("tournament_wins", "tournament_wins")

    generator = RepeatedTournamentWinsBookGenerator(
        random_source=random.Random(5), difficulty="easy", theme="tennis_training"
    )
    book = generator.generate(theme_page_count=2)
    rows = book.summary_table.rows
    assert len(rows) == 2
    assert rows[0].theme_category_instance_id != rows[1].theme_category_instance_id
    assert rows[0].theme_category_id == rows[1].theme_category_id == "tournament_wins"
    assert len(rows[0].value_ids_by_position) == 4


def test_numeric_value_identity_is_instance_scoped_and_strict() -> None:
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category = tennis.category_by_id("tournament_wins")
    instance = tennis.create_category_instance(
        category_id="tournament_wins", random_source=random.Random(11), instance_index=3
    )
    assert category.values == ()
    for value in instance.selected_values:
        assert instance.value_by_id(value.id).numeric_value == value.numeric_value
        rebuilt = category.parse_generated_numeric_value_id(
            value.id, instance_id=instance.instance_id
        )
        assert rebuilt.id == value.id
        assert rebuilt.numeric_value == value.numeric_value
    for bad_id in (
        "unknown_17",
        "wrong_category_12",
        "tournament_wins_4_value_8",
        "tournament_wins_3_value_999",
        "tournament_wins_3_value_nope",
    ):
        with pytest.raises(ValueError):
            category.parse_generated_numeric_value_id(bad_id, instance_id=instance.instance_id)
        with pytest.raises(ValueError):
            instance.value_by_id(bad_id)


def test_invalid_numeric_category_definitions_are_rejected() -> None:
    from logical_puzzle_generator.themes.registry import (
        LocalizedText,
        ThemeCategoryDefinition,
        ThemeWording,
    )

    text = LocalizedText("x", "x")
    valid_wording = ThemeWording(
        direct_assignment=text,
        child_with_theme_nominative=text,
        child_with_theme_dative=text,
        numeric_exact=text,
        numeric_position_exact=text,
        numeric_more=text,
        numeric_fewer=text,
        numeric_twice=text,
        unit_singular=text,
        unit_plural=text,
    )
    with pytest.raises(TypeError):
        ThemeCategoryDefinition("bad", text, (), valid_wording, True, True, 8)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ThemeCategoryDefinition("bad", text, (), valid_wording, True, -1, 8)
    with pytest.raises(ValueError):
        ThemeCategoryDefinition("bad", text, (), valid_wording, True, 2, 4)
    with pytest.raises(ValueError):
        ThemeCategoryDefinition("bad", text, (), valid_wording, True, 13, 16)
    incomplete = ThemeWording(text, text, text)
    with pytest.raises(ValueError):
        ThemeCategoryDefinition("bad", text, (), incomplete, True, 2, 8)


def test_theme_category_instance_rejects_noncanonical_values() -> None:
    from dataclasses import replace

    from logical_puzzle_generator.themes.registry import (
        LocalizedText,
        ThemeCategoryInstance,
        ThemeValue,
    )

    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    text_category = tennis.category_by_id("training")
    canonical_text_values = text_category.values[:4]
    ThemeCategoryInstance(text_category, "training_1", canonical_text_values)
    altered_text = replace(canonical_text_values[0], label=LocalizedText("Altered", "Verändert"))
    with pytest.raises(ValueError, match="canonical registered"):
        ThemeCategoryInstance(
            text_category, "training_1", (altered_text, *canonical_text_values[1:])
        )
    numeric_text = replace(canonical_text_values[0], numeric_value=3)
    with pytest.raises(ValueError, match="numeric values"):
        ThemeCategoryInstance(
            text_category, "training_1", (numeric_text, *canonical_text_values[1:])
        )

    numeric_category = tennis.category_by_id("tournament_wins")
    numeric_instance = tennis.create_category_instance(
        category_id="tournament_wins", random_source=random.Random(15), instance_index=1
    )
    ThemeCategoryInstance(
        numeric_category, numeric_instance.instance_id, numeric_instance.selected_values
    )
    first = numeric_instance.selected_values[0]
    altered_numeric = ThemeValue(
        first.id,
        LocalizedText("Altered", "Verändert"),
        first.short_label,
        first.subject_phrase,
        first.numeric_value,
    )
    with pytest.raises(ValueError, match="canonical generated"):
        ThemeCategoryInstance(
            numeric_category,
            numeric_instance.instance_id,
            (altered_numeric, *numeric_instance.selected_values[1:]),
        )
    mismatched_numeric = replace(first, numeric_value=(first.numeric_value or 0) + 1)
    with pytest.raises(ValueError, match="does not match"):
        ThemeCategoryInstance(
            numeric_category,
            numeric_instance.instance_id,
            (mismatched_numeric, *numeric_instance.selected_values[1:]),
        )
    with pytest.raises(ValueError, match="non-empty"):
        ThemeCategoryInstance(numeric_category, "", numeric_instance.selected_values)
    with pytest.raises(ValueError, match="unique"):
        ThemeCategoryInstance(numeric_category, numeric_instance.instance_id, (first, first))


@pytest.mark.parametrize(("difficulty", "anchors"), [("easy", 2), ("medium", 1), ("hard", 0)])
def test_tournament_wins_final_quality_and_difficulty_by_seed_range(
    difficulty: str, anchors: int
) -> None:
    from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint

    for seed in range(1, 4):
        puzzle = PuzzleGenerator(
            random_source=random.Random(seed),
            difficulty=difficulty,
            theme="tennis_training",
            category="tournament_wins",
            max_attempts=100,
        ).generate(select_child_items(random.Random(7)))
        assert Solver().solve(puzzle, stop_after=2).has_unique_solution
        assert len(puzzle.clues) == len(puzzle.constraints)
        assert any(
            isinstance(constraint, (NumericDifferenceConstraint, NumericMultipleConstraint))
            for constraint in puzzle.constraints
        )
        assert (
            sum(
                isinstance(constraint, FixedPositionConstraint)
                and constraint.item.category_id == "children"
                for constraint in puzzle.constraints
            )
            == anchors
        )


def test_selected_seeds_retain_difference_and_multiple_clues() -> None:
    diff_puzzle = PuzzleGenerator(
        random_source=random.Random(1),
        difficulty="easy",
        theme="tennis_training",
        category="tournament_wins",
    ).generate(select_child_items(random.Random(7)))
    multiple_puzzle = PuzzleGenerator(
        random_source=random.Random(2),
        difficulty="easy",
        theme="tennis_training",
        category="tournament_wins",
    ).generate(select_child_items(random.Random(7)))
    assert any(
        isinstance(constraint, NumericDifferenceConstraint)
        for constraint in diff_puzzle.constraints
    )
    assert any(
        isinstance(constraint, NumericMultipleConstraint)
        for constraint in multiple_puzzle.constraints
    )


def test_difference_rendering_is_seeded_and_can_use_more_or_fewer() -> None:
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    instance = tennis.create_category_instance(
        category_id="tournament_wins", random_source=random.Random(3), instance_index=1
    )
    resolver = ItemPresentationResolver(tennis, instance)
    values = {
        "tournament_wins_1_value_1": 1,
        "tournament_wins_1_value_2": 2,
        "tournament_wins_1_value_5": 5,
        "tournament_wins_1_value_10": 10,
    }
    clue = Clue(
        ClueType.NUMERIC_DIFFERENCE,
        "",
        NumericDifferenceConstraint(
            Item("Mia"), Item("Emma"), 1, category_id="tournament_wins", values_by_id=values
        ),
    )
    first = ClueTextRenderer(
        "en", presentation_resolver=resolver, random_source=random.Random(1)
    ).render_clue(clue)
    again = ClueTextRenderer(
        "en", presentation_resolver=resolver, random_source=random.Random(1)
    ).render_clue(clue)
    other = ClueTextRenderer(
        "en", presentation_resolver=resolver, random_source=random.Random(0)
    ).render_clue(clue)
    assert first == again
    assert first == "Mia won 1 tournament more than Emma."
    assert other == "Emma won 1 tournament fewer than Mia."
    german = ClueTextRenderer(
        "de", presentation_resolver=resolver, random_source=random.Random(0)
    ).render_clue(clue)
    assert german == "Emma gewann 1 Turnier weniger als Mia."


def test_tournament_wins_position_anchor_rendering_is_data_driven() -> None:
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    instance = tennis.create_category_instance(
        category_id="tournament_wins", random_source=random.Random(3), instance_index=1
    )
    value = next(value for value in instance.selected_values if value.numeric_value == 8)
    clue = Clue(
        ClueType.FIXED_POSITION,
        "",
        FixedPositionConstraint(Item(value.id, "tournament_wins"), Position(4)),
    )

    assert (
        ClueTextRenderer(
            "en", presentation_resolver=ItemPresentationResolver(tennis, instance, "en")
        ).render_clue(clue)
        == "The child in Position 4 won 8 tournaments."
    )
    german = ClueTextRenderer(
        "de", presentation_resolver=ItemPresentationResolver(tennis, instance, "de")
    ).render_clue(clue)
    assert german == "Das Kind auf Position 4 gewann 8 Turniere."
    assert "tournament_wins" not in german and "ß" not in german


def test_puzzle_book_numeric_summary_pdf_story_uses_display_values(monkeypatch, tmp_path) -> None:
    from reportlab.platypus import Table

    from logical_puzzle_generator.pdf.generator import PdfGenerator

    class RepeatedTournamentWinsBookGenerator(PuzzleBookGenerator):
        def select_category_ids(self, theme_page_count: int) -> tuple[str, ...]:
            return ("tournament_wins", "tournament_wins")

    book = RepeatedTournamentWinsBookGenerator(
        random_source=random.Random(6), difficulty="easy", theme="tennis_training"
    ).generate(theme_page_count=2)
    captured = {}

    def capture_build(self, output_path, story):
        captured[output_path.name] = story

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    pdf = PdfGenerator(language="en")
    pdf.create_puzzle_book_pdf(book, tmp_path / "puzzle_book.pdf")
    pdf.create_puzzle_book_solution_pdf(book, tmp_path / "puzzle_book_solution.pdf")

    unsolved_table = [
        flowable for flowable in captured["puzzle_book.pdf"] if isinstance(flowable, Table)
    ][-1]
    solved_table = [
        flowable for flowable in captured["puzzle_book_solution.pdf"] if isinstance(flowable, Table)
    ][-1]
    assert len(book.summary_table.rows) == 2
    assert all(cell == "" for row in unsolved_table._cellvalues[1:] for cell in row[1:])
    solved_cells = [cell for row in solved_table._cellvalues[1:] for cell in row]
    assert "Tournament Wins" in [row[0] for row in solved_table._cellvalues[1:]]
    assert all(not str(cell).startswith("tournament_wins_") for cell in solved_cells)
    for row in book.summary_table.rows:
        assert row.theme_category_instance_id in {
            p.metadata.theme_category_instance_id for p in book.theme_puzzles if p.metadata
        }
        assert all(
            value_id.startswith(f"{row.theme_category_instance_id}_value_")
            for value_id in row.value_ids_by_position
        )


def test_neutral_generated_numeric_category_uses_generic_value_ids() -> None:
    from logical_puzzle_generator.themes.registry import (
        LocalizedText,
        ThemeCategoryDefinition,
        ThemeDefinition,
        ThemeWording,
    )

    text = LocalizedText("count", "Anzahl")
    wording = ThemeWording(
        direct_assignment=text,
        child_with_theme_nominative=text,
        child_with_theme_dative=text,
        numeric_exact=text,
        numeric_position_exact=text,
        numeric_more=text,
        numeric_fewer=text,
        numeric_twice=text,
        unit_singular=LocalizedText("item", "Element"),
        unit_plural=LocalizedText("items", "Elemente"),
    )
    category = ThemeCategoryDefinition(
        "sample_count", text, (), wording, is_numeric=True, numeric_minimum=1, numeric_maximum=12
    )
    theme = ThemeDefinition("sample_theme", text, (category,))
    instance = theme.create_category_instance(
        category_id="sample_count", random_source=random.Random(2), instance_index=1
    )
    assert instance.instance_id == "sample_count_1"
    assert len(instance.selected_value_ids) == 4
    assert all(
        value_id.startswith("sample_count_1_value_") for value_id in instance.selected_value_ids
    )
    assert all("wins" not in value_id for value_id in instance.selected_value_ids)
    parsed = category.parse_generated_numeric_value_id(
        instance.selected_value_ids[0], instance_id=instance.instance_id
    )
    assert parsed.id == instance.selected_value_ids[0]
    assert instance.value_by_id(parsed.id) == parsed
    with pytest.raises(ValueError):
        category.parse_generated_numeric_value_id(parsed.id, instance_id="sample_count_2")
    unselected = "sample_count_1_value_7"
    if unselected in instance.selected_value_ids:
        unselected = "sample_count_1_value_11"
    category.parse_generated_numeric_value_id(unselected, instance_id=instance.instance_id)
    with pytest.raises(ValueError):
        instance.value_by_id(unselected)


def test_numeric_value_id_parser_rejects_required_malformed_cases() -> None:
    tennis = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category = tennis.category_by_id("tournament_wins")
    instance_id = "tournament_wins_3"
    for bad_id in (
        "",
        "unknown_17",
        "wrong_category_value_12",
        "tournament_wins_4_value_8",
        "tournament_wins_3_wins_8",
        "tournament_wins_3_value_999",
        "tournament_wins_3_value_nope",
        "tournament_wins_3_value_",
        "tournament_wins_3_value_-1",
    ):
        with pytest.raises((TypeError, ValueError)):
            category.parse_generated_numeric_value_id(bad_id, instance_id=instance_id)
    with pytest.raises(TypeError):
        category.parse_generated_numeric_value_id(123, instance_id=instance_id)  # type: ignore[arg-type]
    text_category = tennis.category_by_id("training")
    with pytest.raises(ValueError):
        text_category.parse_generated_numeric_value_id(
            "training_1_value_2", instance_id="training_1"
        )
