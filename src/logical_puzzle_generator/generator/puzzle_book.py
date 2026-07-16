from __future__ import annotations

import random
from dataclasses import dataclass

from logical_puzzle_generator.generator.difficulty import (
    Difficulty,
    DifficultyPolicy,
    PuzzleBookDifficultyMode,
    PuzzleBookDifficultyPlan,
    PuzzleBookDifficultyPlanner,
)
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.random_streams import derived_random
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
    value_ids_by_position: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.theme_category_id, str) or not self.theme_category_id:
            raise ValueError("SummaryRow requires a non-empty theme_category_id.")
        if (
            not isinstance(self.theme_category_instance_id, str)
            or not self.theme_category_instance_id
        ):
            raise ValueError("SummaryRow requires a non-empty theme_category_instance_id.")
        if not self.value_ids_by_position:
            raise ValueError("SummaryRow requires value IDs ordered by position.")
        if any(
            not isinstance(value_id, str) or not value_id for value_id in self.value_ids_by_position
        ):
            raise ValueError("SummaryRow value IDs must be non-empty strings.")
        if len(set(self.value_ids_by_position)) != len(self.value_ids_by_position):
            raise ValueError("SummaryRow value IDs must be distinct by position.")


@dataclass(frozen=True, slots=True)
class SummaryTable:
    position_ids: tuple[int, ...]
    child_names_by_position: tuple[str, ...]
    rows: tuple[SummaryRow, ...]

    def __post_init__(self) -> None:
        if not self.position_ids:
            raise ValueError("SummaryTable requires at least one position.")
        if any(
            isinstance(position, bool) or not isinstance(position, int) or position < 1
            for position in self.position_ids
        ):
            raise ValueError("SummaryTable positions must be positive integers.")
        expected = tuple(range(1, len(self.position_ids) + 1))
        if self.position_ids != expected:
            raise ValueError("SummaryTable positions must be ordered and contiguous from 1.")
        if len(self.child_names_by_position) != len(self.position_ids):
            raise ValueError("SummaryTable child names must match the position count.")
        if any(
            not isinstance(child_name, str) or not child_name
            for child_name in self.child_names_by_position
        ):
            raise ValueError("SummaryTable child names must be non-empty strings.")
        for row in self.rows:
            if len(row.value_ids_by_position) != len(self.position_ids):
                raise ValueError("SummaryRow values must match the SummaryTable position count.")


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
                    value_ids_by_position=tuple(values),
                )
            )
        return SummaryTable(
            position_ids=tuple(range(1, len(ordered_children) + 1)),
            child_names_by_position=tuple(child.name for child in ordered_children),
            rows=tuple(rows),
        )


class PuzzleBookGenerator:
    """Generate PuzzleBooks from the selected theme registry data."""

    def __init__(
        self,
        *,
        seed: int | None = None,
        random_source: random.Random | None = None,
        difficulty: Difficulty | PuzzleBookDifficultyMode | str = Difficulty.EASY,
        theme: str | None = None,
        max_attempts: int = 100,
        child_count: int = DEFAULT_CHILD_COUNT,
    ) -> None:
        if seed is not None and random_source is not None:
            raise ValueError("Specify either seed or random_source, not both.")
        self._base_seed = self._establish_base_seed(seed=seed, random_source=random_source)
        self._difficulty_mode = self._normalize_difficulty_mode(difficulty)
        self._theme = DEFAULT_THEME_REGISTRY.resolve(
            theme or DEFAULT_THEME_ID,
            self._stream("puzzle_book.theme"),
        )
        self._max_attempts = max_attempts
        if child_count != DEFAULT_CHILD_COUNT:
            raise ValueError("PuzzleBook generation requires exactly four children.")
        self._child_count = child_count

    @property
    def available_category_ids(self) -> tuple[str, ...]:
        """Return category IDs registered on the selected theme definition."""

        return tuple(category.id for category in self._theme.categories)

    def _establish_base_seed(self, *, seed: int | None, random_source: random.Random | None) -> int:
        if seed is not None:
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise TypeError("PuzzleBook seed must be an integer.")
            return seed
        if random_source is not None:
            return random_source.getrandbits(64)
        return random.SystemRandom().getrandbits(64)

    def _stream(self, namespace: str) -> random.Random:
        return derived_random(self._base_seed, namespace)

    def _theme_page_random(
        self, theme_page_index: int, category_id: str, occurrence_index: int
    ) -> random.Random:
        return self._stream(
            f"puzzle_book.theme_page.{theme_page_index}.{category_id}.{occurrence_index}"
        )

    def select_category_ids(self, theme_page_count: int) -> tuple[str, ...]:
        """Select category IDs for theme pages from the theme definition."""

        if theme_page_count < 0:
            raise ValueError("Theme page count must not be negative.")
        if theme_page_count == 0:
            return ()

        category_random = self._stream("puzzle_book.categories")
        category_ids = self.available_category_ids
        if not category_ids:
            raise ValueError(f"Theme '{self._theme.id}' does not define any categories.")

        if theme_page_count <= len(category_ids):
            return tuple(category_random.sample(category_ids, k=theme_page_count))

        selected = list(category_random.sample(category_ids, k=len(category_ids)))
        while len(selected) < theme_page_count:
            selected.append(category_random.choice(category_ids))
        return tuple(selected)

    def generate(
        self,
        *,
        theme_page_count: int,
    ) -> PuzzleBook:
        """Generate a PuzzleBook."""

        plan = self._resolve_difficulty_plan(theme_page_count)
        children = select_child_items(self._stream("puzzle_book.children"), count=self._child_count)
        position_puzzle = self._generate_position_puzzle(children, plan.position_difficulty)
        if position_puzzle.solution is None:
            raise ValueError("Position puzzle requires a solution for fixed PuzzleBook positions.")
        fixed_child_positions = dict(position_puzzle.solution.assignment.positions)
        category_ids = self.select_category_ids(theme_page_count)
        occurrence_counts: dict[str, int] = {}
        theme_puzzles: list[Puzzle] = []
        for theme_page_index, (category_id, page_difficulty) in enumerate(
            zip(category_ids, plan.theme_page_difficulties, strict=True),
            start=1,
        ):
            occurrence_counts[category_id] = occurrence_counts.get(category_id, 0) + 1
            theme_puzzles.append(
                PuzzleGenerator(
                    random_source=self._theme_page_random(
                        theme_page_index, category_id, occurrence_counts[category_id]
                    ),
                    difficulty=page_difficulty,
                    theme=self._theme.id,
                    category=category_id,
                    category_instance_index=occurrence_counts[category_id],
                    max_attempts=self._max_attempts,
                    fixed_child_positions=fixed_child_positions,
                ).generate(children)
            )
        self._validate_generated_plan(position_puzzle, theme_puzzles, plan)
        book = PuzzleBook(
            theme=self._theme,
            children=children,
            position_puzzle=position_puzzle,
            theme_puzzles=tuple(theme_puzzles),
        )
        return book

    def _generate_position_puzzle(
        self, children: tuple[Item, ...], difficulty: Difficulty
    ) -> Puzzle:
        return PuzzleGenerator(
            random_source=self._stream("puzzle_book.position"),
            difficulty=difficulty,
            max_attempts=self._max_attempts,
        ).generate(children)

    def _resolve_difficulty_plan(self, theme_page_count: int) -> PuzzleBookDifficultyPlan:
        planner = PuzzleBookDifficultyPlanner(self._stream("puzzle_book.difficulty"))
        if self._difficulty_mode is PuzzleBookDifficultyMode.MIXED:
            return planner.mixed(theme_page_count)
        return planner.uniform(self._difficulty_mode, theme_page_count)

    def _normalize_difficulty_mode(
        self, difficulty: Difficulty | PuzzleBookDifficultyMode | str | None
    ) -> Difficulty | PuzzleBookDifficultyMode:
        if difficulty is None:
            return Difficulty.EASY
        if difficulty is PuzzleBookDifficultyMode.MIXED:
            return difficulty
        if (
            isinstance(difficulty, str)
            and difficulty.strip().lower() == PuzzleBookDifficultyMode.MIXED.value
        ):
            return PuzzleBookDifficultyMode.MIXED
        concrete = DifficultyPolicy().normalize(difficulty)
        if concrete is None:
            return Difficulty.EASY
        return concrete

    def _validate_generated_plan(
        self,
        position_puzzle: Puzzle,
        theme_puzzles: list[Puzzle],
        plan: PuzzleBookDifficultyPlan,
    ) -> None:
        if position_puzzle.metadata is None:
            raise ValueError("Position puzzle metadata is required.")
        if position_puzzle.metadata.difficulty != plan.position_difficulty.metadata_value:
            raise ValueError("Position puzzle difficulty does not match the resolved plan.")
        if len(theme_puzzles) != len(plan.theme_page_difficulties):
            raise ValueError("Theme puzzle count does not match the resolved difficulty plan.")
        for puzzle, difficulty in zip(theme_puzzles, plan.theme_page_difficulties, strict=True):
            if puzzle.metadata is None:
                raise ValueError("Theme puzzle metadata is required.")
            if puzzle.metadata.difficulty != difficulty.metadata_value:
                raise ValueError("Theme puzzle difficulty does not match the resolved plan.")
