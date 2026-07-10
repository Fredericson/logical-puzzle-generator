from __future__ import annotations

import random
from collections.abc import Iterable

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.engine.validator import Validator
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.metadata import Metadata
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution

from .clue_generator import ClueGenerator
from .clue_reducer import ClueReducer
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
        clue_reducer: ClueReducer | None = None,
        max_attempts: int = 100,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("PuzzleGenerator requires at least one attempt.")

        self._solution_generator = (
            solution_generator
            if solution_generator is not None
            else SolutionGenerator(random_source)
        )
        self._clue_generator = clue_generator if clue_generator is not None else ClueGenerator()
        self._validator = validator if validator is not None else Validator()
        self._clue_reducer = (
            clue_reducer if clue_reducer is not None else ClueReducer(self._validator)
        )
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

        last_failure = "generation did not run"

        for attempt in range(1, self._max_attempts + 1):
            try:
                solution = self._solution_generator.generate(source)
                failure = self._solution_failure(solution, items)
                if failure is not None:
                    last_failure = f"attempt {attempt}: {failure}"
                    continue

                constraints = self._derive_constraints(solution)
                failure = self._constraints_failure(constraints, solution)
                if failure is not None:
                    last_failure = f"attempt {attempt}: {failure}"
                    continue

                clues = self._clue_generator.generate(constraints)
                failure = self._clues_failure(clues)
                if failure is not None:
                    last_failure = f"attempt {attempt}: {failure}"
                    continue

                puzzle = Puzzle(
                    items=items,
                    constraints=constraints,
                    clues=clues,
                    metadata=self._metadata_from_source(source),
                    solution=solution,
                )

                if not self._validator.has_unique_solution(puzzle):
                    last_failure = (
                        f"attempt {attempt}: generated puzzle is not uniquely "
                        "solvable before clue reduction"
                    )
                    continue

                reduced = self._clue_reducer.reduce(puzzle)
                failure = self._reduced_puzzle_failure(reduced, items, solution)
                if failure is not None:
                    last_failure = f"attempt {attempt}: {failure}"
                    continue

                if not self._validator.has_unique_solution(reduced):
                    last_failure = (
                        f"attempt {attempt}: reduced clue set is not uniquely " "solvable"
                    )
                    continue

                return reduced
            except Exception as exc:
                last_failure = f"attempt {attempt}: {exc.__class__.__name__}: {exc}"

        raise RuntimeError(
            "Unable to generate a valid uniquely solvable puzzle within "
            f"{self._max_attempts} attempts. Last failure: {last_failure}."
        )

    def _solution_failure(
        self,
        solution: object,
        items: list[Item],
    ) -> str | None:
        if not isinstance(solution, Solution):
            return "solution generator did not return a Solution"

        if set(solution.positions) != set(items):
            return "generated solution does not assign exactly the puzzle items"

        positions = list(solution.positions.values())
        expected_positions = {Position(index) for index in range(1, len(items) + 1)}
        if set(positions) != expected_positions or len(set(positions)) != len(positions):
            return "generated solution does not contain a unique complete position set"

        return None

    def _constraints_failure(
        self,
        constraints: object,
        solution: Solution,
    ) -> str | None:
        if not isinstance(constraints, list):
            return "constraint derivation did not return a list"

        if not constraints:
            return "constraint derivation produced no constraints"

        if any(not isinstance(constraint, Constraint) for constraint in constraints):
            return "constraint derivation produced a non-Constraint value"

        if any(not constraint.matches(solution.assignment) for constraint in constraints):
            return "derived constraints do not match the generated solution"

        return None

    def _clues_failure(
        self,
        clues: object,
    ) -> str | None:
        if not isinstance(clues, list):
            return "clue generation did not return a list"

        if not clues:
            return "clue generation produced no clues"

        if any(not isinstance(clue, Clue) for clue in clues):
            return "clue generation produced a non-Clue value"

        return None

    def _reduced_puzzle_failure(
        self,
        puzzle: object,
        items: list[Item],
        solution: Solution,
    ) -> str | None:
        if not isinstance(puzzle, Puzzle):
            return "clue reduction did not return a Puzzle"

        if puzzle.items != items:
            return "clue reduction changed puzzle items"

        if puzzle.solution != solution:
            return "clue reduction changed the puzzle solution"

        constraints_failure = self._constraints_failure(puzzle.constraints, solution)
        if constraints_failure is not None:
            return f"clue reduction returned invalid constraints: {constraints_failure}"

        clues_failure = self._clues_failure(puzzle.clues)
        if clues_failure is not None:
            return f"clue reduction returned invalid clues: {clues_failure}"

        return None

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
