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


def test_future_puzzle_book_pages_share_one_child_roster_reference() -> None:
    children = (Item("Emma"), Item("Mia"), Item("Noah"), Item("Tim"))
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    category_instance = theme.create_category_instance(category_id="bag_colour", random_source=random.Random(1))
    position_page = PuzzlePage(kind="position", children=children, puzzle=_puzzle(children), solution=_puzzle(children).solution)
    category_page = PuzzlePage(
        kind="category",
        children=children,
        puzzle=_puzzle(children),
        solution=_puzzle(children).solution,
        category_instance=category_instance,
    )
    summary = SummaryTable(
        children=children,
        rows=(SummaryTableRow(category_instance.instance_id, "Bag colour", (("Emma", "Red"),)),),
    )

    plan = PuzzleBookPlan(children, theme, position_page, (category_page,), summary)

    assert plan.position_page.children is children
    assert plan.category_pages[0].children is children
    assert plan.summary_table is not None
    assert plan.summary_table.children is children
    assert [row.category_instance_id for row in plan.summary_table.rows] == ["bag_colour_1"]


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
