from __future__ import annotations

import random
from dataclasses import replace
from collections import Counter
from collections.abc import Iterable

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.engine.solver import Solver
from logical_puzzle_generator.engine.validator import Validator
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.metadata import Metadata
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution

from .clue_generator import ClueGenerator
from .clue_reducer import ClueReducer
from .constraint_distribution_policy import ConstraintDistributionPolicy
from .difficulty import Difficulty, DifficultyPolicy
from .fixed_position_generator import FixedPositionGenerator
from .puzzle_template import PuzzleTemplate
from .solution_generator import SolutionGenerator

QUALITY_CANDIDATE_COUNT = 8

# Rewards one-time use of each clue meaning so varied clue sets beat repetitive ones.
QUALITY_UNIQUE_MEANING_WEIGHT = 12
# Endpoint anchors are intentionally not rewarded so random fixed-position slots are not biased to endpoints.
QUALITY_ENDPOINT_WEIGHT = 0
# Undirected adjacency clues add useful relational variety without revealing direction.
QUALITY_ADJACENT_WEIGHT = 3
# Direct left/right clues are strong but still relational, so they receive adjacency-level weight.
QUALITY_DIRECT_RELATION_WEIGHT = 3
# Duplicate meanings are allowed, but each repeat makes the clue set feel more mechanical.
QUALITY_DUPLICATE_MEANING_PENALTY = 5
# Dominant meanings are penalized separately to avoid clue sets made mostly from one pattern.
QUALITY_DOMINANT_MEANING_PENALTY = 3

QUALITY_FAR_LEFT_MEANING = "far_left"
QUALITY_FAR_RIGHT_MEANING = "far_right"


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
        fixed_position_generator: FixedPositionGenerator | None = None,
        difficulty: Difficulty | str | None = None,
        max_attempts: int = 100,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("PuzzleGenerator requires at least one attempt.")

        self._random = random_source if random_source is not None else random.Random()
        self._clue_generator = clue_generator
        self._validator = validator if validator is not None else Validator()
        self._solver = Solver()
        self._clue_reducer = (
            clue_reducer if clue_reducer is not None else ClueReducer(self._validator)
        )
        self._difficulty_policy = DifficultyPolicy()
        self._distribution_policy = ConstraintDistributionPolicy()
        self._fixed_position_generator = (
            fixed_position_generator
            if fixed_position_generator is not None
            else FixedPositionGenerator(self._random, solution_generator=solution_generator)
        )
        self._requested_difficulty = self._difficulty_policy.normalize(difficulty)
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

        selected_difficulty = self._select_difficulty()
        last_failure = "generation did not run"
        candidates: list[Puzzle] = []

        for attempt in range(1, self._max_attempts + 1):
            try:
                candidate, failure = self._generate_candidate(source, items, selected_difficulty)
                if failure is not None:
                    last_failure = f"attempt {attempt}: {failure}"
                    continue

                candidates.append(candidate)
                if len(candidates) >= QUALITY_CANDIDATE_COUNT:
                    break
            except Exception as exc:
                last_failure = f"attempt {attempt}: {exc.__class__.__name__}: {exc}"

        if candidates:
            return max(candidates, key=self._quality_score)

        raise RuntimeError(
            "Unable to generate a valid uniquely solvable "
            f"{selected_difficulty.cli_value} puzzle within {self._max_attempts} attempts. "
            "Difficulty is defined by final visible FixedPositionConstraint clues "
            "(easy == 2, medium == 1, hard == 0). "
            f"Last failure: {last_failure}."
        )

    def _generate_candidate(
        self,
        source: PuzzleTemplate | Puzzle | Iterable[Item],
        items: list[Item],
        difficulty: Difficulty,
    ) -> tuple[Puzzle, None] | tuple[None, str]:
        fixed_position_constraints, solution = self._fixed_position_generator.generate(items, difficulty)
        failure = self._solution_failure(solution, items)
        if failure is not None:
            return None, failure

        constraints = [
            *fixed_position_constraints,
            *self._derive_relational_constraints(solution),
        ]
        failure = self._constraints_failure(constraints, solution)
        if failure is not None:
            return None, failure

        if not self._distribution_policy.accepts(constraints, difficulty):
            return None, "generated constraints have a poor clue type distribution"

        clue_generator = (
            self._clue_generator if self._clue_generator is not None else ClueGenerator(len(items))
        )
        clues = clue_generator.generate(constraints)
        failure = self._clues_failure(clues)
        if failure is not None:
            return None, failure

        puzzle = Puzzle(
            items=items,
            constraints=constraints,
            clues=clues,
            metadata=self._metadata_from_source(source),
            solution=solution,
        )

        if not self._validator.has_unique_solution(puzzle):
            return None, "generated puzzle is not uniquely solvable before clue reduction"

        try:
            reduced = self._clue_reducer.reduce(puzzle, difficulty=difficulty)
        except TypeError:
            reduced = self._clue_reducer.reduce(puzzle)
        failure = self._reduced_puzzle_failure(reduced, items, solution)
        if failure is not None:
            return None, failure

        if not self._validator.has_unique_solution(reduced):
            return None, "reduced clue set is not uniquely solvable"

        if not self._difficulty_policy.matches(reduced, difficulty):
            count = self._difficulty_policy.fixed_position_count(reduced)
            return None, (
                f"reduced puzzle has {count} visible FixedPositionConstraint clues, "
                f"which does not match requested difficulty {difficulty.cli_value}"
            )

        reduced = self._with_estimated_difficulty(reduced, difficulty)

        return reduced, None

    def _quality_score(self, puzzle: Puzzle) -> tuple[int, int, int, int, int]:
        meanings = [self._quality_clue_meaning(clue, len(puzzle.items)) for clue in puzzle.clues]
        counts = Counter(meanings)
        unique_type_count = len(counts)
        endpoint_count = 0
        adjacent_count = counts[ClueType.ADJACENT.value]
        direct_count = (
            counts[ClueType.DIRECT_LEFT_OF.value] + counts[ClueType.DIRECT_RIGHT_OF.value]
        )
        duplicate_penalty = sum(count - 1 for count in counts.values() if count > 1)
        dominant_penalty = max(counts.values(), default=0) - 1

        distribution_score = self._distribution_policy.score(puzzle.constraints)

        return (
            distribution_score
            + unique_type_count * QUALITY_UNIQUE_MEANING_WEIGHT
            + endpoint_count * QUALITY_ENDPOINT_WEIGHT
            + adjacent_count * QUALITY_ADJACENT_WEIGHT
            + direct_count * QUALITY_DIRECT_RELATION_WEIGHT
            - duplicate_penalty * QUALITY_DUPLICATE_MEANING_PENALTY
            - dominant_penalty * QUALITY_DOMINANT_MEANING_PENALTY,
            unique_type_count,
            endpoint_count + adjacent_count + direct_count,
            -len(puzzle.clues),
            -duplicate_penalty,
        )

    def _quality_clue_meaning(self, clue: Clue, item_count: int) -> str:
        constraint = clue.constraint
        if isinstance(constraint, FixedPositionConstraint):
            if constraint.position.index == 1:
                return QUALITY_FAR_LEFT_MEANING
            if constraint.position.index == item_count:
                return QUALITY_FAR_RIGHT_MEANING
            return ClueType.FIXED_POSITION.value

        return clue.clue_type.value

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

        if len(puzzle.clues) != len(puzzle.constraints):
            return "clue reduction returned mismatched clue and constraint counts"

        for clue, constraint in zip(puzzle.clues, puzzle.constraints, strict=True):
            if clue.constraint is not constraint:
                return "clue reduction returned a clue without its corresponding constraint"

        result = self._solver.solve(puzzle, stop_after=2)
        if not result.has_unique_solution:
            return "clue reduction returned a puzzle without exactly one solution"

        if result.solutions[0] != solution.assignment:
            return "clue reduction returned a puzzle with a different unique solution"

        return None

    def _select_difficulty(self) -> Difficulty:
        if self._requested_difficulty is not None:
            return self._requested_difficulty
        return self._random.choice(list(Difficulty))

    def _derive_relational_constraints(
        self,
        solution: Solution,
    ) -> list[Constraint]:
        ordered_items = sorted(
            solution.positions,
            key=lambda item: solution.assignment.position_of(item).index,
        )

        constraints: list[Constraint] = []
        seen: set[tuple[object, ...]] = set()
        item_count = len(ordered_items)

        if item_count == 1:
            return constraints

        adjacent_constraints: list[Constraint] = []
        for left_item, right_item in zip(ordered_items, ordered_items[1:], strict=False):
            constraint_cls = self._random.choice(
                [
                    DirectLeftOfConstraint,
                    DirectRightOfConstraint,
                    AdjacentConstraint,
                ]
            )
            if constraint_cls is DirectLeftOfConstraint:
                adjacent_constraints.append(DirectLeftOfConstraint(left_item, right_item))
            elif constraint_cls is DirectRightOfConstraint:
                adjacent_constraints.append(DirectRightOfConstraint(right_item, left_item))
            else:
                adjacent_constraints.append(AdjacentConstraint(left_item, right_item))

        self._random.shuffle(adjacent_constraints)
        for constraint in adjacent_constraints:
            self._append_unique(constraints, seen, constraint)

        relational_constraints: list[Constraint] = []
        for left_index, left_item in enumerate(ordered_items):
            for right_item in ordered_items[left_index + 2 :]:
                if self._random.choice([True, False]):
                    relational_constraints.append(LeftOfConstraint(left_item, right_item))
                else:
                    relational_constraints.append(RightOfConstraint(right_item, left_item))

        self._random.shuffle(relational_constraints)
        for constraint in relational_constraints:
            self._append_unique(constraints, seen, constraint)

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

        if isinstance(constraint, DirectLeftOfConstraint):
            return (
                DirectLeftOfConstraint,
                constraint.left,
                constraint.right,
            )

        if isinstance(constraint, DirectRightOfConstraint):
            return (
                DirectRightOfConstraint,
                constraint.right,
                constraint.left,
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
            return self._copy_metadata(source.metadata)

        return None

    def _with_estimated_difficulty(self, puzzle: Puzzle, difficulty: Difficulty) -> Puzzle:
        metadata = self._copy_metadata(puzzle.metadata)
        if metadata is not None:
            metadata.difficulty = difficulty.metadata_value

        return Puzzle(
            items=puzzle.items,
            constraints=puzzle.constraints,
            clues=puzzle.clues,
            metadata=metadata,
            solution=puzzle.solution,
        )

    def _copy_metadata(self, metadata: Metadata | None) -> Metadata | None:
        if metadata is None:
            return None

        return replace(metadata)
