from __future__ import annotations

import random
from dataclasses import dataclass

from logical_puzzle_generator.generator.difficulty import Difficulty
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.themes.children import DEFAULT_CHILD_COUNT, select_child_items
from logical_puzzle_generator.themes.registry import (
    DEFAULT_THEME_ID,
    DEFAULT_THEME_REGISTRY,
    ThemeDefinition,
)


@dataclass(frozen=True, slots=True)
class SummaryRow:
    theme_category_id: str
    theme_category_instance_id: str
    value_ids_by_child: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SummaryTable:
    child_ids: tuple[str, ...]
    rows: tuple[SummaryRow, ...]


@dataclass(frozen=True, slots=True)
class PuzzleBook:
    """A generated PuzzleBook for one selected theme."""

    theme: ThemeDefinition
    children: tuple[Item, ...]
    position_puzzle: Puzzle
    theme_puzzles: tuple[Puzzle, ...]

    @property
    def theme_id(self) -> str:
        return self.theme.id

    @property
    def pages(self) -> tuple[Puzzle, ...]:
        return (self.position_puzzle, *self.theme_puzzles)

    @property
    def stable_children(self) -> tuple[Item, ...]:
        if self.position_puzzle.solution is None:
            raise ValueError("Position puzzle requires a solution for PuzzleBook ordering.")
        assignment = self.position_puzzle.solution.assignment
        return tuple(sorted(self.children, key=lambda child: assignment.position_of(child).index))

    @property
    def summary_table(self) -> SummaryTable:
        ordered_children = self.stable_children
        rows: list[SummaryRow] = []
        for puzzle in self.theme_puzzles:
            if puzzle.metadata is None:
                raise ValueError("Theme puzzle metadata is required for summary generation.")
            if puzzle.solution is None:
                raise ValueError("Theme puzzle solution is required for summary generation.")
            if puzzle.metadata.theme_id != self.theme.id:
                raise ValueError("PuzzleBook summary cannot mix themes.")
            theme_items = [
                item
                for category in puzzle.categories
                for item in category.items
                if item.category_id != CHILDREN_CATEGORY_ID
            ]
            assignment = puzzle.solution.assignment
            values: list[str] = []
            for child in ordered_children:
                child_position = assignment.position_of(child)
                theme_item = next(
                    item for item in theme_items if assignment.position_of(item) == child_position
                )
                values.append(theme_item.name)
            rows.append(
                SummaryRow(
                    theme_category_id=puzzle.metadata.theme_category_id or "",
                    theme_category_instance_id=puzzle.metadata.theme_category_instance_id or "",
                    value_ids_by_child=tuple(values),
                )
            )
        return SummaryTable(
            child_ids=tuple(child.name for child in ordered_children), rows=tuple(rows)
        )


class PuzzleBookGenerator:
    """Generate PuzzleBooks from the selected theme registry data."""

    def __init__(
        self,
        *,
        random_source: random.Random | None = None,
        difficulty: Difficulty | str | None = None,
        theme: str | None = None,
        max_attempts: int = 100,
        child_count: int = DEFAULT_CHILD_COUNT,
    ) -> None:
        self._random = random_source if random_source is not None else random.Random()
        self._difficulty = difficulty
        self._theme = DEFAULT_THEME_REGISTRY.resolve(theme or DEFAULT_THEME_ID, self._random)
        self._max_attempts = max_attempts
        if child_count != DEFAULT_CHILD_COUNT:
            raise ValueError("PuzzleBook generation requires exactly four children.")
        self._child_count = child_count

    @property
    def available_category_ids(self) -> tuple[str, ...]:
        """Return category IDs registered on the selected theme definition."""

        return tuple(category.id for category in self._theme.categories)

    def select_category_ids(self, theme_page_count: int) -> tuple[str, ...]:
        """Select category IDs for theme pages from the theme definition."""

        if theme_page_count < 0:
            raise ValueError("Theme page count must not be negative.")
        if theme_page_count == 0:
            return ()

        category_ids = self.available_category_ids
        if not category_ids:
            raise ValueError(f"Theme '{self._theme.id}' does not define any categories.")

        if theme_page_count <= len(category_ids):
            return tuple(self._random.sample(category_ids, k=theme_page_count))

        selected = list(self._random.sample(category_ids, k=len(category_ids)))
        while len(selected) < theme_page_count:
            selected.append(self._random.choice(category_ids))
        return tuple(selected)

    def generate(
        self,
        *,
        theme_page_count: int,
    ) -> PuzzleBook:
        """Generate a PuzzleBook."""

        children = select_child_items(self._random, count=self._child_count)
        position_puzzle = self._generate_position_puzzle(children)
        category_ids = self.select_category_ids(theme_page_count)
        occurrence_counts: dict[str, int] = {}
        theme_puzzles: list[Puzzle] = []
        for category_id in category_ids:
            occurrence_counts[category_id] = occurrence_counts.get(category_id, 0) + 1
            theme_puzzles.append(
                PuzzleGenerator(
                    random_source=self._random,
                    difficulty=self._difficulty,
                    theme=self._theme.id,
                    category=category_id,
                    category_instance_index=occurrence_counts[category_id],
                    max_attempts=self._max_attempts,
                ).generate(children)
            )
        book = PuzzleBook(
            theme=self._theme,
            children=children,
            position_puzzle=position_puzzle,
            theme_puzzles=tuple(theme_puzzles),
        )
        return book

    def _generate_position_puzzle(self, children: tuple[Item, ...]) -> Puzzle:
        return PuzzleGenerator(
            random_source=self._random,
            difficulty=self._difficulty,
            max_attempts=self._max_attempts,
        ).generate(children)
