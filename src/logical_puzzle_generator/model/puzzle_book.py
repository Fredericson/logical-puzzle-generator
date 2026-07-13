from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution
from logical_puzzle_generator.themes.registry import ThemeCategoryInstance, ThemeDefinition

PageKind = Literal["position", "category"]


@dataclass(frozen=True, slots=True)
class PuzzlePage:
    """Future PuzzleBook page contract.

    Commit 12.2 still renders one puzzle page at a time. This model records the
    intended future invariant that every page references the same immutable child
    roster instead of generating page-local names.
    """

    kind: PageKind
    children: tuple[Item, ...]
    puzzle: Puzzle
    solution: Solution
    category_instance: ThemeCategoryInstance | None = None

    def __post_init__(self) -> None:
        if self.kind == "position" and self.category_instance is not None:
            raise ValueError("The universal position page must not have a theme category.")
        if self.kind == "category" and self.category_instance is None:
            raise ValueError("A category page requires a selected theme category instance.")


@dataclass(frozen=True, slots=True)
class SummaryTableRow:
    """One future summary-table row for one solved theme-category page."""

    category_instance_id: str
    category_label: str
    values_by_child_id: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class SummaryTable:
    """Future final PuzzleBook page contract.

    The summary table is not a logic puzzle and has no solver step. Its rows are
    a presentation of already solved category pages. The position page is not a
    row because it only establishes child ordering.
    """

    children: tuple[Item, ...]
    rows: tuple[SummaryTableRow, ...]


@dataclass(frozen=True, slots=True)
class PuzzleBookPlan:
    """Future PuzzleBook contract; generation is intentionally deferred."""

    children: tuple[Item, ...]
    theme: ThemeDefinition
    position_page: PuzzlePage
    category_pages: tuple[PuzzlePage, ...]
    summary_table: SummaryTable | None = None

    def __post_init__(self) -> None:
        if self.position_page.kind != "position":
            raise ValueError("PuzzleBookPlan requires a universal position page first.")
        if self.position_page.children != self.children:
            raise ValueError("The position page must reference the stable PuzzleBook child roster.")
        for page in self.category_pages:
            if page.kind != "category":
                raise ValueError("PuzzleBookPlan category_pages may contain only category pages.")
            if page.children != self.children:
                raise ValueError("Every category page must reference the stable PuzzleBook child roster.")
        if self.summary_table is not None and self.summary_table.children != self.children:
            raise ValueError("The summary table must use the stable PuzzleBook child roster.")
