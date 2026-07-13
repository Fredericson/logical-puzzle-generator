from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.puzzle_book import (
    PuzzleBookPlan,
    PuzzlePage,
    SummaryTable,
    SummaryTableRow,
)
from logical_puzzle_generator.model.solution import Solution
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY


def _puzzle(children: tuple[Item, ...]) -> Puzzle:
    assignment = Assignment({child: Position(index + 1) for index, child in enumerate(children)})
    return Puzzle(items=list(children), constraints=[], solution=Solution(assignment))


def test_future_puzzle_book_pages_share_one_child_roster_by_value() -> None:
    children = (Item("Emma"), Item("Mia"), Item("Noah"), Item("Tim"))
    same_children = tuple(Item(child.name) for child in children)
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category_instance = theme.create_category_instance(category_id="bag_colour", random_source=random.Random(1))
    position_page = PuzzlePage(kind="position", children=same_children, puzzle=_puzzle(same_children), solution=_puzzle(same_children).solution)
    category_page = PuzzlePage(
        kind="category",
        children=same_children,
        puzzle=_puzzle(same_children),
        solution=_puzzle(same_children).solution,
        category_instance=category_instance,
    )
    summary = SummaryTable(
        children=same_children,
        rows=(SummaryTableRow(category_instance.instance_id, "Bag colour", (("Emma", "Red"),)),),
    )

    plan = PuzzleBookPlan(children, theme, position_page, (category_page,), summary)

    assert plan.position_page.children == children
    assert plan.position_page.children is not children
    assert plan.category_pages[0].children == children
    assert plan.summary_table is not None
    assert plan.summary_table.children == children
    assert [row.category_instance_id for row in plan.summary_table.rows] == ["bag_colour_1"]


def test_future_puzzle_book_rejects_different_child_or_order() -> None:
    children = (Item("Emma"), Item("Mia"), Item("Noah"), Item("Tim"))
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    position_page = PuzzlePage(kind="position", children=children, puzzle=_puzzle(children), solution=_puzzle(children).solution)

    reordered = (Item("Mia"), Item("Emma"), Item("Noah"), Item("Tim"))
    with pytest.raises(ValueError, match="stable PuzzleBook child roster"):
        PuzzleBookPlan(
            children,
            theme,
            PuzzlePage(kind="position", children=reordered, puzzle=_puzzle(reordered), solution=_puzzle(reordered).solution),
            (),
        )

    different = (Item("Emma"), Item("Mia"), Item("Noah"), Item("Lara"))
    category_instance = theme.create_category_instance(category_id="bag_colour", random_source=random.Random(1))
    with pytest.raises(ValueError, match="stable PuzzleBook child roster"):
        PuzzleBookPlan(
            children,
            theme,
            position_page,
            (
                PuzzlePage(
                    kind="category",
                    children=different,
                    puzzle=_puzzle(different),
                    solution=_puzzle(different).solution,
                    category_instance=category_instance,
                ),
            ),
        )


def test_position_page_is_not_a_summary_row_or_category_page() -> None:
    children = (Item("Emma"), Item("Mia"), Item("Noah"), Item("Tim"))
    page = PuzzlePage(kind="position", children=children, puzzle=_puzzle(children), solution=_puzzle(children).solution)

    assert page.category_instance is None
    with pytest.raises(ValueError, match="must not have a theme category"):
        PuzzlePage(
            kind="position",
            children=children,
            puzzle=_puzzle(children),
            solution=_puzzle(children).solution,
            category_instance=DEFAULT_THEME_REGISTRY.resolve("tennis_training").create_category_instance(
                category_id="training", random_source=random.Random(1)
            ),
        )
