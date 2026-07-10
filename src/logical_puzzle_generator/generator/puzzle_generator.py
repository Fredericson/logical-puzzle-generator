from __future__ import annotations

import random
from collections.abc import Iterable

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.engine.validator import Validator
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.metadata import Metadata
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution

from .clue_generator import ClueGenerator
from .puzzle_template import PuzzleTemplate
from .solution_generator import SolutionGenerator


class PuzzleGenerator:
    """
    Coordinates the complete Version 1.0 puzzle generation pipeline.

    The generator intentionally owns constraint derivation as a private
    implementation detail. Version 1.0 does not expose a public
    ConstraintGenerator component.
    """

    def __init__(
        self,
        *_legacy_dependencies: object,
        random_source: random.Random | None = None,
        solution_generator: SolutionGenerator | None = None,
        clue_generator: ClueGenerator | None = None,
        validator: Validator | None = None,
        max_attempts: int = 100,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("PuzzleGenerator requires at least one attempt.")

        self._solution_generator = (
            solution_generator
            if solution_generator is not None
            else SolutionGenerator(random_source)
        )
        self._clue_generator = (
            clue_generator
            if clue_generator is not None
            else ClueGenerator()
        )
        self._validator = validator if validator is not None else Validator()
        self._max_attempts = max_attempts

    def generate(
        self,
        source: PuzzleTemplate | Puzzle | Iterable[Item],
    ) -> Puzzle:
        """
        Generate a uniquely solvable puzzle from a template, puzzle, or items.
        """
        items = self._items_from_source(source)
        self._validate_items(items)

        for _attempt in range(self._max_attempts):
            solution = self._solution_generator.generate(source)
            constraints = self._derive_constraints(solution)
            clues = self._clue_generator.generate(constraints)

            puzzle = Puzzle(
                items=items,
                constraints=constraints,
                clues=clues,
                metadata=self._metadata_from_source(source),
                solution=solution,
            )

            if self._validator.has_unique_solution(puzzle):
                return puzzle

        raise RuntimeError(
            "Unable to generate a uniquely solvable puzzle within "
            f"{self._max_attempts} attempts."
        )

    def _derive_constraints(
        self,
        solution: Solution,
    ) -> list[Constraint]:
        ordered_items = sorted(
            solution.positions,
            key=lambda item: solution.assignment.position_of(item),
        )

        constraints: list[Constraint] = []
        seen: set[tuple[object, ...]] = set()

        if len(ordered_items) == 1:
            item = ordered_items[0]
            self._append_unique(
                constraints,
                seen,
                FixedPositionConstraint(
                    item,
                    solution.assignment.position_of(item),
                ),
            )
            return constraints

        for left_item, right_item in zip(
            ordered_items,
            ordered_items[1:],
            strict=False,
        ):
            self._append_unique(
                constraints,
                seen,
                LeftOfConstraint(left_item, right_item),
            )

        return constraints

    def _append_unique(
        self,
        constraints: list[Constraint],
        seen: set[tuple[object, ...]],
        constraint: Constraint,
    ) -> None:
        key = self._constraint_key(constraint)
        if key in seen:
            return

        constraints.append(constraint)
        seen.add(key)

    def _constraint_key(self, constraint: Constraint) -> tuple[object, ...]:
        if isinstance(constraint, FixedPositionConstraint):
            return (
                FixedPositionConstraint,
                constraint.item,
                constraint.position,
            )

        if isinstance(constraint, LeftOfConstraint):
            return (
                LeftOfConstraint,
                constraint.left,
                constraint.right,
            )

        if isinstance(constraint, RightOfConstraint):
            return (
                RightOfConstraint,
                constraint.right,
                constraint.left,
            )

        if isinstance(constraint, AdjacentConstraint):
            return (
                AdjacentConstraint,
                frozenset((constraint.first, constraint.second)),
            )

        return (constraint.__class__, constraint.description)

    def _items_from_source(
        self,
        source: PuzzleTemplate | Puzzle | Iterable[Item],
    ) -> list[Item]:
        if isinstance(source, PuzzleTemplate):
            if not source.categories:
                return []

            return list(source.players.items)

        if isinstance(source, Puzzle):
            return list(source.items)

        return list(source)

    def _validate_items(self, items: list[Item]) -> None:
        if not items:
            raise ValueError("A puzzle requires at least one item.")

        if any(not isinstance(item, Item) for item in items):
            raise TypeError("PuzzleGenerator requires model.Item instances.")

        if len(set(items)) != len(items):
            raise ValueError("A puzzle requires unique items.")

    def _metadata_from_source(
        self,
        source: PuzzleTemplate | Puzzle | Iterable[Item],
    ) -> Metadata | None:
        if isinstance(source, PuzzleTemplate):
            return Metadata(
                title=source.title,
                theme=source.theme,
                difficulty=1,
            )

        if isinstance(source, Puzzle):
            return source.metadata

        return None
