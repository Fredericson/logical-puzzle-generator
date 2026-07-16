from __future__ import annotations

import random
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum

from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.numeric import ExactNumericValueConstraint
from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.themes.registry import ThemeCategoryInstance


class Difficulty(Enum):
    """Selectable Version 1 puzzle difficulty."""

    EASY = ("easy", 1)
    MEDIUM = ("medium", 2)
    HARD = ("hard", 3)

    def __init__(self, cli_value: str, metadata_value: int) -> None:
        self.cli_value = cli_value
        self.metadata_value = metadata_value


class PuzzleBookDifficultyMode(Enum):
    """PuzzleBook-only Difficulty request modes."""

    MIXED = "mixed"


CONCRETE_DIFFICULTIES = (Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD)


@dataclass(frozen=True, slots=True)
class PuzzleBookDifficultyPlan:
    """Resolved concrete Difficulty sequence for one PuzzleBook."""

    position_difficulty: Difficulty
    theme_page_difficulties: tuple[Difficulty, ...]

    def __post_init__(self) -> None:
        if self.position_difficulty not in CONCRETE_DIFFICULTIES:
            raise ValueError("Position difficulty must be easy, medium, or hard.")
        if any(
            difficulty not in CONCRETE_DIFFICULTIES for difficulty in self.theme_page_difficulties
        ):
            raise ValueError("Theme page difficulties must be easy, medium, or hard.")


class PuzzleBookDifficultyPlanner:
    """Resolve uniform and mixed PuzzleBook difficulty plans without generating puzzles."""

    _MAX_SHUFFLE_ATTEMPTS = 64

    def __init__(self, random_source: random.Random | None = None) -> None:
        self._random = random_source if random_source is not None else random.Random()
        self._policy = DifficultyPolicy()

    def uniform(
        self, difficulty: Difficulty | str, theme_page_count: int
    ) -> PuzzleBookDifficultyPlan:
        self._validate_theme_page_count(theme_page_count)
        concrete = self._require_concrete(difficulty)
        return PuzzleBookDifficultyPlan(concrete, (concrete,) * theme_page_count)

    def mixed(self, theme_page_count: int) -> PuzzleBookDifficultyPlan:
        self._validate_theme_page_count(theme_page_count)
        puzzle_page_count = theme_page_count + 1
        counts = self._balanced_counts(puzzle_page_count)
        multiset = [
            difficulty for difficulty in CONCRETE_DIFFICULTIES for _ in range(counts[difficulty])
        ]
        sequence = self._seeded_sequence(multiset)
        return PuzzleBookDifficultyPlan(sequence[0], tuple(sequence[1:]))

    def _balanced_counts(self, puzzle_page_count: int) -> dict[Difficulty, int]:
        base, remainder = divmod(puzzle_page_count, len(CONCRETE_DIFFICULTIES))
        counts = {difficulty: base for difficulty in CONCRETE_DIFFICULTIES}
        remainder_receivers = list(CONCRETE_DIFFICULTIES)
        self._random.shuffle(remainder_receivers)
        for difficulty in remainder_receivers[:remainder]:
            counts[difficulty] += 1
        return counts

    def _seeded_sequence(self, multiset: list[Difficulty]) -> list[Difficulty]:
        if len(multiset) < 3:
            sequence = list(multiset)
            self._random.shuffle(sequence)
            return sequence
        for _ in range(self._MAX_SHUFFLE_ATTEMPTS):
            candidate = list(multiset)
            self._random.shuffle(candidate)
            if self._max_run_length(candidate) <= 2:
                return candidate
        return self._interleaved_fallback(multiset)

    def _interleaved_fallback(self, multiset: list[Difficulty]) -> list[Difficulty]:
        remaining = Counter(multiset)
        sequence: list[Difficulty] = []
        while remaining:
            choices = sorted(
                remaining,
                key=lambda difficulty: (-remaining[difficulty], difficulty.metadata_value),
            )
            for difficulty in choices:
                if len(sequence) >= 2 and sequence[-1] is difficulty and sequence[-2] is difficulty:
                    continue
                sequence.append(difficulty)
                remaining[difficulty] -= 1
                if remaining[difficulty] == 0:
                    del remaining[difficulty]
                break
            else:
                # Balanced counts should make this unreachable; keep deterministic behavior.
                difficulty = choices[0]
                sequence.append(difficulty)
                remaining[difficulty] -= 1
                if remaining[difficulty] == 0:
                    del remaining[difficulty]
        return sequence

    def _max_run_length(self, difficulties: list[Difficulty]) -> int:
        longest = current = 0
        previous: Difficulty | None = None
        for difficulty in difficulties:
            current = current + 1 if difficulty is previous else 1
            longest = max(longest, current)
            previous = difficulty
        return longest

    def _require_concrete(self, difficulty: Difficulty | str) -> Difficulty:
        concrete = self._policy.normalize(difficulty)
        if concrete is None:
            raise ValueError("A concrete difficulty is required.")
        return concrete

    def _validate_theme_page_count(self, theme_page_count: int) -> None:
        if isinstance(theme_page_count, bool) or not isinstance(theme_page_count, int):
            raise TypeError("Theme page count must be a non-negative integer.")
        if theme_page_count < 0:
            raise ValueError("Theme page count must not be negative.")


class DifficultyContext(Enum):
    """Page task used when counting visible direct assignments."""

    POSITION_PAGE = "position_page"
    STANDALONE_THEMED_PAGE = "standalone_themed_page"
    FIXED_CHILD_THEME_PAGE = "fixed_child_theme_page"


class DifficultyPolicy:
    """Classify final visible constraints by page-local direct assignments."""

    def normalize(self, difficulty: Difficulty | str | None) -> Difficulty | None:
        if difficulty is None:
            return None
        if isinstance(difficulty, Difficulty):
            return difficulty
        if isinstance(difficulty, str):
            normalized = difficulty.strip().lower()
            for candidate in Difficulty:
                if candidate.cli_value == normalized:
                    return candidate
        allowed = ", ".join(d.cli_value for d in Difficulty)
        raise ValueError(f"Unsupported difficulty {difficulty!r}. Expected one of: {allowed}.")

    def classify(self, puzzle_or_constraints: Puzzle | Iterable[Constraint]) -> Difficulty:
        count = self.fixed_position_count(puzzle_or_constraints)
        if count == 2:
            return Difficulty.EASY
        if count == 1:
            return Difficulty.MEDIUM
        if count == 0:
            return Difficulty.HARD
        raise ValueError(
            f"Invalid Version 1 fixed-position clue count {count}. Expected exactly 2, 1, or 0."
        )

    def metadata_value(self, puzzle_or_constraints: Puzzle | Iterable[Constraint]) -> int:
        return self.classify(puzzle_or_constraints).metadata_value

    def estimate(self, puzzle_or_constraints: Puzzle | Iterable[Constraint]) -> int:
        return self.metadata_value(puzzle_or_constraints)

    def matches(
        self,
        puzzle_or_constraints: Puzzle | Iterable[Constraint],
        difficulty: Difficulty | str,
    ) -> bool:
        try:
            return self.classify(puzzle_or_constraints) is self.normalize(difficulty)
        except ValueError:
            return False

    def fixed_position_count(self, puzzle_or_constraints: Puzzle | Iterable[Constraint]) -> int:
        constraints = (
            puzzle_or_constraints.constraints
            if isinstance(puzzle_or_constraints, Puzzle)
            else puzzle_or_constraints
        )
        return sum(
            isinstance(constraint, FixedPositionConstraint)
            and getattr(constraint.item, "category_id", CHILDREN_CATEGORY_ID)
            == CHILDREN_CATEGORY_ID
            for constraint in constraints
        )

    def required_fixed_position_count(self, difficulty: Difficulty | str) -> int:
        return self.required_direct_assignment_count(difficulty)

    def required_direct_assignment_count(self, difficulty: Difficulty | str) -> int:
        requested = self.normalize(difficulty)
        if requested is Difficulty.EASY:
            return 2
        if requested is Difficulty.MEDIUM:
            return 1
        if requested is Difficulty.HARD:
            return 0
        raise ValueError("A concrete difficulty is required.")

    def direct_assignment_count(
        self,
        puzzle_or_constraints: Puzzle | Iterable[Constraint],
        *,
        context: DifficultyContext,
        fixed_child_positions: Mapping[Item, Position] | None = None,
        theme_items: Iterable[Item] | None = None,
        category_instance: ThemeCategoryInstance | None = None,
    ) -> int:
        constraints = (
            puzzle_or_constraints.constraints
            if isinstance(puzzle_or_constraints, Puzzle)
            else puzzle_or_constraints
        )
        if context in {
            DifficultyContext.POSITION_PAGE,
            DifficultyContext.STANDALONE_THEMED_PAGE,
        }:
            return self.fixed_position_count(constraints)
        if context is DifficultyContext.FIXED_CHILD_THEME_PAGE:
            if fixed_child_positions is not None and theme_items is not None:
                return len(
                    self.theme_direct_assignment_identities(
                        constraints,
                        fixed_child_positions=fixed_child_positions,
                        theme_items=theme_items,
                        category_instance=category_instance,
                    )
                )
            return self.raw_theme_direct_constraint_count(constraints)
        raise ValueError(f"Unsupported difficulty context: {context!r}.")

    def raw_theme_direct_constraint_count(
        self, puzzle_or_constraints: Puzzle | Iterable[Constraint]
    ) -> int:
        constraints = (
            puzzle_or_constraints.constraints
            if isinstance(puzzle_or_constraints, Puzzle)
            else puzzle_or_constraints
        )
        return sum(self.is_theme_direct_assignment(constraint) for constraint in constraints)

    def is_theme_direct_assignment(self, constraint: Constraint) -> bool:
        if isinstance(constraint, SamePositionConstraint):
            return (constraint.first.category_id == CHILDREN_CATEGORY_ID) != (
                constraint.second.category_id == CHILDREN_CATEGORY_ID
            )
        if isinstance(constraint, ExactNumericValueConstraint):
            return True
        if isinstance(constraint, FixedPositionConstraint):
            return constraint.item.category_id != CHILDREN_CATEGORY_ID
        return False

    def theme_direct_assignment_identities(
        self,
        puzzle_or_constraints: Puzzle | Iterable[Constraint],
        *,
        fixed_child_positions: Mapping[Item, Position],
        theme_items: Iterable[Item],
        category_instance: ThemeCategoryInstance | None = None,
    ) -> frozenset[tuple[int, str]]:
        constraints = (
            puzzle_or_constraints.constraints
            if isinstance(puzzle_or_constraints, Puzzle)
            else puzzle_or_constraints
        )
        identities = {
            identity
            for constraint in constraints
            if (
                identity := self.theme_direct_assignment_identity(
                    constraint,
                    fixed_child_positions=fixed_child_positions,
                    theme_items=theme_items,
                    category_instance=category_instance,
                )
            )
            is not None
        }
        return frozenset(identities)

    def theme_direct_assignment_identity(
        self,
        constraint: Constraint,
        *,
        fixed_child_positions: Mapping[Item, Position],
        theme_items: Iterable[Item],
        category_instance: ThemeCategoryInstance | None = None,
    ) -> tuple[int, str] | None:
        if not self.is_theme_direct_assignment(constraint):
            return None

        theme_items_by_id = self._theme_items_by_id(
            theme_items, category_instance=category_instance
        )

        if isinstance(constraint, SamePositionConstraint):
            first_is_child = constraint.first.category_id == CHILDREN_CATEGORY_ID
            child = constraint.first if first_is_child else constraint.second
            theme_item = constraint.second if first_is_child else constraint.first
            return (
                self._fixed_child_position_index(child, fixed_child_positions),
                self._validated_theme_item_id(theme_item, theme_items_by_id),
            )

        if isinstance(constraint, FixedPositionConstraint):
            return (
                constraint.position.index,
                self._validated_theme_item_id(constraint.item, theme_items_by_id),
            )

        if isinstance(constraint, ExactNumericValueConstraint):
            if category_instance is None:
                raise ValueError("Exact numeric direct assignments require a category instance.")
            if category_instance.category_id != constraint.category_id:
                raise ValueError(
                    "Exact numeric constraint category does not match the page category."
                )
            matching_values = [
                value
                for value in category_instance.selected_values
                if value.numeric_value == constraint.value
            ]
            if len(matching_values) != 1:
                raise ValueError("Exact numeric direct assignment must match one selected value.")
            value_id = matching_values[0].id
            canonical_item = theme_items_by_id.get(value_id)
            if canonical_item is None:
                raise ValueError("Exact numeric selected value is not present in page theme items.")
            return (
                self._fixed_child_position_index(constraint.child, fixed_child_positions),
                self._validated_theme_item_id(canonical_item, theme_items_by_id),
            )

        return None

    def _fixed_child_position_index(
        self, child: Item, fixed_child_positions: Mapping[Item, Position]
    ) -> int:
        if child not in fixed_child_positions:
            raise ValueError("Direct child-to-theme assignment child is not fixed on this page.")
        return fixed_child_positions[child].index

    def _theme_items_by_id(
        self,
        theme_items: Iterable[Item],
        *,
        category_instance: ThemeCategoryInstance | None = None,
    ) -> dict[str, Item]:
        theme_items_by_id: dict[str, Item] = {}
        selected_value_ids = (
            set(category_instance.selected_value_ids) if category_instance is not None else None
        )
        for item in theme_items:
            if item.category_id == CHILDREN_CATEGORY_ID:
                raise ValueError("Selected page Theme items must be non-child items.")
            if item.name in theme_items_by_id:
                raise ValueError("Selected page Theme items must have unique IDs.")
            if category_instance is not None:
                if item.category_id != category_instance.category_id:
                    raise ValueError(
                        "Selected page Theme item category does not match the page category."
                    )
                if selected_value_ids is not None and item.name not in selected_value_ids:
                    raise ValueError(
                        "Selected page Theme item is not part of the category instance."
                    )
            theme_items_by_id[item.name] = item
        return theme_items_by_id

    def _validated_theme_item_id(
        self, theme_item: Item, theme_items_by_id: Mapping[str, Item]
    ) -> str:
        if theme_item.category_id == CHILDREN_CATEGORY_ID:
            raise ValueError("Theme direct assignment expected a non-child theme item.")
        canonical_item = theme_items_by_id.get(theme_item.name)
        if canonical_item is None:
            raise ValueError("Theme direct assignment item is not selected on this page.")
        if canonical_item != theme_item:
            raise ValueError("Theme direct assignment item does not match the selected page item.")
        return canonical_item.name

    def can_remove_to_match(
        self,
        puzzle_or_constraints: Puzzle | Iterable[Constraint],
        difficulty: Difficulty | str,
    ) -> bool:
        count = self.fixed_position_count(puzzle_or_constraints)
        try:
            return count == self.required_fixed_position_count(difficulty)
        except ValueError:
            return False
