from __future__ import annotations

from collections.abc import Iterable, Mapping
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
            f"Invalid Version 1 fixed-position clue count {count}. " "Expected exactly 2, 1, or 0."
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
            return self.theme_direct_assignment_count(constraints)
        raise ValueError(f"Unsupported difficulty context: {context!r}.")

    def theme_direct_assignment_count(
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

        theme_items_by_id = {item.name: item for item in theme_items}

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
            if value_id not in theme_items_by_id:
                raise ValueError("Exact numeric selected value is not present in page theme items.")
            return (
                self._fixed_child_position_index(constraint.child, fixed_child_positions),
                value_id,
            )

        return None

    def _fixed_child_position_index(
        self, child: Item, fixed_child_positions: Mapping[Item, Position]
    ) -> int:
        if child not in fixed_child_positions:
            raise ValueError("Direct child-to-theme assignment child is not fixed on this page.")
        return fixed_child_positions[child].index

    def _validated_theme_item_id(
        self, theme_item: Item, theme_items_by_id: Mapping[str, Item]
    ) -> str:
        if theme_item.category_id == CHILDREN_CATEGORY_ID:
            raise ValueError("Theme direct assignment expected a non-child theme item.")
        if theme_item.name not in theme_items_by_id:
            raise ValueError("Theme direct assignment item is not selected on this page.")
        return theme_item.name

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
