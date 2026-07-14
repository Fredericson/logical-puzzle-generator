from __future__ import annotations

import random
from dataclasses import replace
from collections import Counter
from collections.abc import Iterable
from itertools import combinations

from logical_puzzle_generator.constraints.adjacent import AdjacentConstraint
from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.constraints.fixed_position import FixedPositionConstraint
from logical_puzzle_generator.constraints.direct_left_of import DirectLeftOfConstraint
from logical_puzzle_generator.constraints.direct_right_of import DirectRightOfConstraint
from logical_puzzle_generator.constraints.left_of import LeftOfConstraint
from logical_puzzle_generator.constraints.right_of import RightOfConstraint
from logical_puzzle_generator.constraints.same_position import SamePositionConstraint
from logical_puzzle_generator.constraints.numeric import (
    ExactNumericValueConstraint,
    NumericDifferenceConstraint,
    NumericMultipleConstraint,
)
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.engine.solver import Solver
from logical_puzzle_generator.engine.validator import Validator
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.category import Category, CategoryType
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.clue_type import ClueType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.metadata import Metadata
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution
from logical_puzzle_generator.themes.registry import (
    DEFAULT_THEME_REGISTRY,
    DEFAULT_THEME_ID,
    ThemeCategoryInstance,
)

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
QUALITY_ADJACENT_WEIGHT = 0
# Direct left/right clues are strong but still relational, so they receive adjacency-level weight.
QUALITY_DIRECT_RELATION_WEIGHT = 0
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
        distribution_policy: ConstraintDistributionPolicy | None = None,
        difficulty: Difficulty | str | None = None,
        theme: str | None = None,
        category: str | None = None,
        category_instance_index: int = 1,
        max_attempts: int = 100,
        fixed_child_positions: dict[Item, Position] | None = None,
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
        self._distribution_policy = (
            distribution_policy
            if distribution_policy is not None
            else ConstraintDistributionPolicy()
        )
        self._fixed_position_generator = (
            fixed_position_generator
            if fixed_position_generator is not None
            else FixedPositionGenerator(self._random, solution_generator=solution_generator)
        )
        self._requested_difficulty = self._difficulty_policy.normalize(difficulty)
        self._themed_mode = theme is not None
        self._theme = (
            DEFAULT_THEME_REGISTRY.resolve(theme, self._random) if self._themed_mode else None
        )
        if category_instance_index < 1:
            raise ValueError("Category instance index must be a positive integer.")
        self._category_id = category
        self._category_instance_index = category_instance_index
        self._max_attempts = max_attempts
        self._fixed_child_positions = fixed_child_positions

    def _select_category_instance(
        self,
        source: PuzzleTemplate | Puzzle | Iterable[Item],
    ) -> ThemeCategoryInstance | None:
        if not self._themed_mode:
            return None
        if self._theme is None:
            raise ValueError("A theme is required for themed generation.")
        if isinstance(source, Puzzle) and source.categories:
            raise ValueError(
                "Themed generation requires raw child items or a PuzzleTemplate, not an already categorized Puzzle."
            )
        return self._theme.create_category_instance(
            category_id=self._category_id,
            random_source=self._random,
            instance_index=self._category_instance_index,
        )

    def generate(
        self,
        source: PuzzleTemplate | Puzzle | Iterable[Item],
    ) -> Puzzle:
        """
        Generate a uniquely solvable puzzle from a template, puzzle, or items.
        """
        items = self._items_from_source(source)
        self._validate_items(items)
        category_instance = self._select_category_instance(source)
        theme_items = (
            [
                Item(value.id, category_id=category_instance.category_id)
                for value in category_instance.selected_values
            ]
            if category_instance is not None
            else []
        )
        all_items = [*items, *theme_items]
        self._current_theme_items = theme_items
        self._current_all_items = all_items
        self._current_category_instance = category_instance

        selected_difficulty = self._select_difficulty()
        last_failure = "generation did not run"
        candidates: list[Puzzle] = []

        for attempt in range(1, self._max_attempts + 1):
            try:
                candidate, failure = self._generate_candidate(source, items, selected_difficulty)
                if failure is not None:
                    last_failure = f"attempt {attempt}: {failure}"
                    continue

                if candidate is None:
                    last_failure = f"attempt {attempt}: candidate generation returned no puzzle"
                    continue

                candidates.append(candidate)
                if len(candidates) >= QUALITY_CANDIDATE_COUNT:
                    break
            except TypeError:
                raise
            except Exception as exc:
                last_failure = f"attempt {attempt}: {exc.__class__.__name__}: {exc}"

        if candidates:
            best_score = max(self._quality_score(candidate) for candidate in candidates)
            best_candidates = [
                candidate
                for candidate in candidates
                if self._quality_score(candidate) == best_score
            ]
            return self._random.choice(best_candidates)

        raise RuntimeError(
            "Unable to generate a valid uniquely solvable "
            f"{selected_difficulty.cli_value} puzzle within {self._max_attempts} attempts. "
            f"{self._difficulty_failure_context()} "
            f"Last failure: {last_failure}."
        )

    def _generate_candidate(
        self,
        source: PuzzleTemplate | Puzzle | Iterable[Item],
        items: list[Item],
        difficulty: Difficulty,
        theme_items: list[Item] | None = None,
        all_items: list[Item] | None = None,
    ) -> tuple[Puzzle, None] | tuple[None, str]:
        theme_items = (
            theme_items if theme_items is not None else getattr(self, "_current_theme_items", [])
        )
        all_items = (
            all_items if all_items is not None else getattr(self, "_current_all_items", items)
        )
        if self._fixed_child_positions is None:
            fixed_position_constraints, child_solution = self._fixed_position_generator.generate(
                items, difficulty
            )
            child_context: dict[Item, Position] = {}
        else:
            self._validate_fixed_child_positions(items)
            fixed_position_constraints = []
            child_solution = Solution(Assignment(dict(self._fixed_child_positions)))
            child_context = dict(self._fixed_child_positions)
        child_failure = self._solution_failure(child_solution, items)
        if child_failure is not None:
            return None, child_failure
        theme_solution = self._solution_generator_for_theme(theme_items) if theme_items else None
        positions = dict(child_solution.positions)
        if theme_solution is not None:
            positions.update(theme_solution.positions)
        solution = Solution(Assignment(positions))
        failure = self._solution_failure(solution, all_items)
        if failure is not None:
            return None, failure

        child_relational_constraints = (
            []
            if self._fixed_child_positions is not None
            else self._derive_relational_constraints(child_solution)
        )
        child_constraints = self._select_visible_constraints(
            fixed_position_constraints,
            child_relational_constraints,
            items=items,
            solution=child_solution,
            source=source,
            difficulty=difficulty,
        )
        thematic_candidates = self._derive_thematic_constraints(solution, items, theme_items)
        thematic_constraints = self._select_thematic_constraints(
            thematic_candidates,
            child_constraints=child_constraints,
            children=items,
            theme_items=theme_items,
            solution=solution,
            difficulty=difficulty,
        )
        if thematic_constraints is None:
            return None, "no bounded uniquely solvable thematic clue subset was found"

        fixed_theme_failure = self._fixed_child_theme_constraints_failure(
            thematic_constraints, difficulty
        )
        if fixed_theme_failure is not None:
            return None, fixed_theme_failure

        constraints = [*child_constraints, *thematic_constraints]
        failure = self._constraints_failure(constraints, solution)
        if failure is not None:
            return None, failure

        if self._fixed_child_positions is None and not self._distribution_policy.accepts(
            child_constraints,
            required_fixed_count=self._difficulty_policy.required_fixed_position_count(difficulty),
            item_count=len(items),
        ):
            return None, "generated constraints have a poor clue type distribution"

        clue_generator = (
            self._clue_generator if self._clue_generator is not None else ClueGenerator(len(items))
        )
        clues = clue_generator.generate(constraints)
        failure = self._clues_failure(clues)
        if failure is not None:
            return None, failure
        fixed_theme_clue_failure = self._fixed_child_theme_clues_failure(
            constraints, clues, difficulty
        )
        if fixed_theme_clue_failure is not None:
            return None, fixed_theme_clue_failure

        puzzle = Puzzle(
            items=items,
            constraints=constraints,
            fixed_positions=child_context,
            categories=self._categories(
                items, theme_items, getattr(self, "_current_category_instance", None)
            ),
            clues=clues,
            metadata=self._metadata_from_source(source),
            solution=solution,
        )

        if not self._validator.has_unique_solution(puzzle):
            return None, "generated puzzle is not uniquely solvable before clue reduction"

        reduced = (
            puzzle
            if self._fixed_child_positions is not None
            else self._clue_reducer.reduce(puzzle, difficulty=difficulty)
        )
        failure = self._reduced_puzzle_failure(reduced, items, solution)
        if failure is not None:
            return None, failure

        if not self._validator.has_unique_solution(reduced):
            return None, "reduced clue set is not uniquely solvable"

        if self._fixed_child_positions is None and not self._difficulty_policy.matches(
            reduced, difficulty
        ):
            count = self._difficulty_policy.fixed_position_count(reduced)
            return None, (
                f"reduced puzzle has {count} visible FixedPositionConstraint clues, "
                f"which does not match requested difficulty {difficulty.cli_value}"
            )

        numeric_failure = self._numeric_quality_failure(reduced)
        if numeric_failure is not None:
            return None, numeric_failure

        reduced = self._with_estimated_difficulty(reduced, difficulty)

        return reduced, None

    def _validate_fixed_child_positions(self, items: list[Item]) -> None:
        mapping = self._fixed_child_positions
        if mapping is None:
            return
        if len(mapping) != len(items):
            raise ValueError("Fixed child positions must contain exactly the page children.")
        if set(mapping) != set(items):
            raise ValueError("Fixed child positions must use exactly the page children.")
        if any(item.category_id != CHILDREN_CATEGORY_ID for item in mapping):
            raise ValueError("Fixed child positions may only contain child items.")
        expected = set(range(1, len(items) + 1))
        actual = {position.index for position in mapping.values()}
        if actual != expected or len(actual) != len(mapping):
            raise ValueError("Fixed child positions must use each page position exactly once.")

    def _numeric_quality_failure(self, puzzle: Puzzle) -> str | None:
        category_instance = getattr(self, "_current_category_instance", None)
        if category_instance is None or not category_instance.definition.is_numeric:
            return None

        relative_count = sum(
            isinstance(constraint, (NumericDifferenceConstraint, NumericMultipleConstraint))
            for constraint in puzzle.constraints
        )
        if relative_count < 1:
            return "numeric puzzle must retain at least one relative arithmetic clue"
        return None

    def _select_visible_constraints(
        self,
        fixed_position_constraints: list[FixedPositionConstraint],
        relational_constraints: list[Constraint],
        *,
        items: list[Item],
        solution: Solution,
        source: PuzzleTemplate | Puzzle | Iterable[Item],
        difficulty: Difficulty,
    ) -> list[Constraint]:
        target_relation_count = self._target_relation_count(len(items), difficulty)
        if target_relation_count is None:
            return [*fixed_position_constraints, *relational_constraints]

        viable_sets: list[list[Constraint]] = []
        for relation_subset in combinations(relational_constraints, target_relation_count):
            constraints = [*fixed_position_constraints, *relation_subset]
            puzzle = Puzzle(
                items=items,
                constraints=constraints,
                clues=[],
                metadata=self._metadata_from_source(source),
                solution=solution,
                fixed_positions=dict(getattr(self, "_fixed_child_positions", {}) or {}),
            )
            if self._solver.solve(puzzle, stop_after=2).has_unique_solution:
                viable_sets.append(constraints)

        if not viable_sets:
            return [*fixed_position_constraints, *relational_constraints]

        best_score = max(
            self._distribution_policy.score(constraints) for constraints in viable_sets
        )
        best_sets = [
            constraints
            for constraints in viable_sets
            if self._distribution_policy.score(constraints) == best_score
        ]
        return self._random.choice(best_sets)

    def _is_child_position_constraint(self, constraint: Constraint) -> bool:
        items: list[Item] = []
        if isinstance(constraint, FixedPositionConstraint):
            items = [constraint.item]
        elif isinstance(constraint, (DirectLeftOfConstraint, LeftOfConstraint)):
            items = [constraint.left, constraint.right]
        elif isinstance(constraint, (DirectRightOfConstraint, RightOfConstraint)):
            items = [constraint.right, constraint.left]
        elif isinstance(constraint, AdjacentConstraint):
            items = [constraint.first, constraint.second]
        return bool(items) and all(item.category_id == CHILDREN_CATEGORY_ID for item in items)

    def _target_relation_count(
        self,
        item_count: int,
        difficulty: Difficulty,
    ) -> int | None:
        if item_count != 4:
            return None
        if difficulty is Difficulty.EASY:
            return 1
        if difficulty is Difficulty.MEDIUM:
            return 2
        if difficulty is Difficulty.HARD:
            return 3
        return None

    def _quality_score(self, puzzle: Puzzle) -> tuple[int, ...]:
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
            *distribution_score,
            unique_type_count * QUALITY_UNIQUE_MEANING_WEIGHT
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

        categories = {item.category_id for item in items}
        for category_id in categories:
            category_items = [item for item in items if item.category_id == category_id]
            positions = [solution.positions[item] for item in category_items]
            expected_positions = {Position(index) for index in range(1, len(category_items) + 1)}
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

    def _solution_generator_for_theme(self, items: list[Item]) -> Solution:
        positions = [Position(index) for index in range(1, len(items) + 1)]
        self._random.shuffle(positions)
        return Solution(Assignment(dict(zip(items, positions, strict=True))))

    def _select_thematic_constraints(
        self,
        candidates: list[Constraint],
        *,
        child_constraints: list[Constraint],
        children: list[Item],
        theme_items: list[Item],
        solution: Solution,
        difficulty: Difficulty,
    ) -> list[Constraint] | None:
        if not candidates:
            return []

        if self._fixed_child_positions is not None:
            return self._select_fixed_child_thematic_constraints(
                candidates,
                children=children,
                theme_items=theme_items,
                solution=solution,
                difficulty=difficulty,
            )

        shuffled = list(candidates)
        self._random.shuffle(shuffled)
        max_subset_size = min(7, len(shuffled))
        max_checked_per_size = 180
        best_subsets: list[tuple[tuple[int, ...], list[Constraint]]] = []

        for subset_size in range(3, max_subset_size + 1):
            checked = 0
            viable: list[tuple[tuple[int, ...], list[Constraint]]] = []
            for subset_tuple in combinations(shuffled, subset_size):
                checked += 1
                subset = list(subset_tuple)
                constraints = [*child_constraints, *subset]
                puzzle = Puzzle(
                    items=children,
                    constraints=constraints,
                    fixed_positions=dict(getattr(self, "_fixed_child_positions", {}) or {}),
                    categories=self._categories(
                        children, theme_items, getattr(self, "_current_category_instance", None)
                    ),
                    clues=[],
                    metadata=self._metadata_from_source(Puzzle(items=children, constraints=[])),
                    solution=solution,
                )
                result = self._solver.solve(puzzle, stop_after=2)
                if result.has_unique_solution and result.solutions[0] == solution.assignment:
                    viable.append((self._thematic_quality_score(subset), subset))
                if checked >= max_checked_per_size:
                    break
            if viable:
                best_score = max(score for score, _ in viable)
                best_subsets = [(score, subset) for score, subset in viable if score == best_score]
                break

        if not best_subsets:
            return None
        return list(self._random.choice(best_subsets)[1])

    def _select_fixed_child_thematic_constraints(
        self,
        candidates: list[Constraint],
        *,
        children: list[Item],
        theme_items: list[Item],
        solution: Solution,
        difficulty: Difficulty,
    ) -> list[Constraint] | None:
        required_direct_count = self._difficulty_policy.required_direct_assignment_count(difficulty)
        category_instance = getattr(self, "_current_category_instance", None)
        direct_variants_by_identity: dict[tuple[int, str], list[Constraint]] = {}
        relative_candidates: list[Constraint] = []
        for constraint in candidates:
            identity = self._difficulty_policy.theme_direct_assignment_identity(
                constraint,
                fixed_child_positions=self._fixed_child_positions or {},
                theme_items=theme_items,
                category_instance=category_instance,
            )
            if identity is None:
                relative_candidates.append(constraint)
            else:
                direct_variants_by_identity.setdefault(identity, []).append(constraint)

        direct_identities = list(direct_variants_by_identity)
        if len(direct_identities) < required_direct_count:
            return None

        self._random.shuffle(direct_identities)
        for variants in direct_variants_by_identity.values():
            self._random.shuffle(variants)
        self._random.shuffle(relative_candidates)
        max_relative_size = min(7 - required_direct_count, len(relative_candidates))
        best_subsets: list[tuple[tuple[int, int, int, int], list[Constraint]]] = []

        for identity_tuple in combinations(direct_identities, required_direct_count):
            direct_subset = [
                self._random.choice(direct_variants_by_identity[identity])
                for identity in identity_tuple
            ]
            for relative_size in range(1, max_relative_size + 1):
                checked = 0
                for relative_tuple in combinations(relative_candidates, relative_size):
                    checked += 1
                    subset = [*direct_subset, *relative_tuple]
                    constraints = list(subset)
                    puzzle = Puzzle(
                        items=children,
                        constraints=constraints,
                        fixed_positions=dict(self._fixed_child_positions or {}),
                        categories=self._categories(
                            children,
                            theme_items,
                            category_instance,
                        ),
                        clues=[],
                        metadata=self._metadata_from_source(Puzzle(items=children, constraints=[])),
                        solution=solution,
                    )
                    if (
                        category_instance is not None
                        and category_instance.definition.is_numeric
                        and not any(
                            isinstance(
                                constraint,
                                (NumericDifferenceConstraint, NumericMultipleConstraint),
                            )
                            for constraint in subset
                        )
                    ):
                        continue
                    result = self._solver.solve(puzzle, stop_after=2)
                    if result.has_unique_solution and result.solutions[0] == solution.assignment:
                        best_subsets.append((self._thematic_quality_score(subset), subset))
                    if checked >= 180:
                        break

        if not best_subsets:
            return None
        best_score = max(score for score, _ in best_subsets)
        best_tied_subsets = [subset for score, subset in best_subsets if score == best_score]
        return list(self._random.choice(best_tied_subsets))

    def _fixed_child_theme_constraints_failure(
        self, thematic_constraints: list[Constraint], difficulty: Difficulty
    ) -> str | None:
        if self._fixed_child_positions is None:
            return None
        required = self._difficulty_policy.required_direct_assignment_count(difficulty)
        count = self._fixed_child_theme_direct_assignment_count(thematic_constraints)
        if count != required:
            return (
                f"fixed-child Theme page retained {count} direct Theme assignments, "
                f"expected {required}"
            )
        if any(
            self._is_child_position_constraint(constraint) for constraint in thematic_constraints
        ):
            return "fixed-child Theme pages must not contain visible child-position constraints"
        return self._fixed_child_theme_duplicate_direct_assignment_failure(thematic_constraints)

    def _fixed_child_theme_clues_failure(
        self, constraints: list[Constraint], clues: list[Clue], difficulty: Difficulty
    ) -> str | None:
        if self._fixed_child_positions is None:
            return None
        required = self._difficulty_policy.required_direct_assignment_count(difficulty)
        count = self._fixed_child_theme_direct_assignment_count(constraints)
        if count != required:
            return (
                f"fixed-child Theme page rendered {count} direct Theme assignments, "
                f"expected {required}"
            )
        if len(clues) != len(constraints):
            return "fixed-child Theme page clue and constraint counts differ"
        for clue, constraint in zip(clues, constraints, strict=True):
            if clue.constraint is not constraint:
                return "fixed-child Theme page clue/constraint ordering is inconsistent"
        if any(self._is_child_position_constraint(constraint) for constraint in constraints):
            return "fixed-child Theme pages must not render child-position clues"
        return self._fixed_child_theme_duplicate_direct_assignment_failure(constraints)

    def _fixed_child_theme_direct_assignment_count(self, constraints: list[Constraint]) -> int:
        return len(
            self._difficulty_policy.theme_direct_assignment_identities(
                constraints,
                fixed_child_positions=self._fixed_child_positions or {},
                theme_items=getattr(self, "_current_theme_items", ()),
                category_instance=getattr(self, "_current_category_instance", None),
            )
        )

    def _fixed_child_theme_duplicate_direct_assignment_failure(
        self, constraints: list[Constraint]
    ) -> str | None:
        raw_count = self._difficulty_policy.theme_direct_assignment_count(constraints)
        identity_count = self._fixed_child_theme_direct_assignment_count(constraints)
        if raw_count != identity_count:
            return "fixed-child Theme page contains duplicate direct assignment identities"
        return None

    def _difficulty_failure_context(self) -> str:
        if self._fixed_child_positions is not None:
            return (
                "Difficulty is defined by final visible direct Theme assignments "
                "(easy == 2, medium == 1, hard == 0)."
            )
        return (
            "Difficulty is defined by final visible child FixedPositionConstraint clues "
            "(easy == 2, medium == 1, hard == 0)."
        )

    def _thematic_quality_score(self, constraints: list[Constraint]) -> tuple[int, int, int, int]:
        family_counts = Counter(type(constraint) for constraint in constraints)
        same_position_count = family_counts[SamePositionConstraint]
        relation_count = sum(
            family_counts[constraint_type]
            for constraint_type in (
                DirectLeftOfConstraint,
                DirectRightOfConstraint,
                LeftOfConstraint,
                RightOfConstraint,
                AdjacentConstraint,
            )
        )
        dominant_count = max(family_counts.values(), default=0)
        return (
            len(family_counts),
            relation_count,
            -same_position_count,
            -dominant_count,
        )

    def _derive_thematic_constraints(
        self, solution: Solution, children: list[Item], theme_items: list[Item]
    ) -> list[Constraint]:
        if not theme_items:
            return []
        constraints: list[Constraint] = []
        seen: set[tuple[object, ...]] = set()
        assignment = solution.assignment

        category_instance = getattr(self, "_current_category_instance", None)
        if category_instance is not None and category_instance.definition.is_numeric:
            self._append_numeric_constraints(
                constraints, seen, children, theme_items, assignment, category_instance
            )
        else:
            for child in children:
                child_position = assignment.position_of(child)
                paired = next(
                    item for item in theme_items if assignment.position_of(item) == child_position
                )
                self._append_unique(constraints, seen, SamePositionConstraint(child, paired))

        for theme_item in theme_items:
            self._append_unique(
                constraints,
                seen,
                FixedPositionConstraint(theme_item, assignment.position_of(theme_item)),
            )

        for child in children:
            for theme_item in theme_items:
                self._append_positional_pair_constraints(
                    constraints, seen, child, theme_item, assignment
                )

        for left_index, first_theme in enumerate(theme_items):
            for second_theme in theme_items[left_index + 1 :]:
                self._append_positional_pair_constraints(
                    constraints, seen, first_theme, second_theme, assignment
                )

        self._random.shuffle(constraints)
        return constraints

    def _append_numeric_constraints(
        self,
        constraints: list[Constraint],
        seen: set[tuple[object, ...]],
        children: list[Item],
        theme_items: list[Item],
        assignment: Assignment,
        category_instance: ThemeCategoryInstance,
    ) -> None:
        numeric_values_by_id: dict[str, int] = {}
        for value in category_instance.selected_values:
            if value.numeric_value is None:
                raise ValueError("Numeric category instances require numeric values.")
            numeric_values_by_id[value.id] = value.numeric_value
        child_values: dict[Item, int] = {}
        for child in children:
            child_position = assignment.position_of(child)
            paired = next(
                item for item in theme_items if assignment.position_of(item) == child_position
            )
            child_values[child] = numeric_values_by_id[paired.name]

        # Generate all exact child-to-number candidates. The final selector keeps
        # the exact direct-assignment count required by page difficulty.
        exact_children = list(children)
        self._random.shuffle(exact_children)
        for child in exact_children:
            self._append_unique(
                constraints,
                seen,
                ExactNumericValueConstraint(
                    child,
                    child_values[child],
                    category_id=category_instance.category_id,
                    values_by_id=numeric_values_by_id,
                ),
            )

        for first, second in combinations(children, 2):
            first_value, second_value = child_values[first], child_values[second]
            if first_value == second_value:
                continue
            greater, lesser = (first, second) if first_value > second_value else (second, first)
            self._append_unique(
                constraints,
                seen,
                NumericDifferenceConstraint(
                    greater,
                    lesser,
                    abs(first_value - second_value),
                    category_id=category_instance.category_id,
                    values_by_id=numeric_values_by_id,
                ),
            )
            if first_value == 2 * second_value:
                self._append_unique(
                    constraints,
                    seen,
                    NumericMultipleConstraint(
                        first,
                        second,
                        2,
                        category_id=category_instance.category_id,
                        values_by_id=numeric_values_by_id,
                    ),
                )
            if second_value == 2 * first_value:
                self._append_unique(
                    constraints,
                    seen,
                    NumericMultipleConstraint(
                        second,
                        first,
                        2,
                        category_id=category_instance.category_id,
                        values_by_id=numeric_values_by_id,
                    ),
                )

    def _append_positional_pair_constraints(
        self,
        constraints: list[Constraint],
        seen: set[tuple[object, ...]],
        first: Item,
        second: Item,
        assignment: Assignment,
    ) -> None:
        first_position = assignment.position_of(first).index
        second_position = assignment.position_of(second).index
        distance = second_position - first_position
        if distance == 0:
            return
        if abs(distance) == 1:
            if distance < 0:
                first, second = second, first
            self._append_unique(constraints, seen, DirectLeftOfConstraint(first, second))
            self._append_unique(constraints, seen, DirectRightOfConstraint(second, first))
            self._append_unique(constraints, seen, AdjacentConstraint(first, second))
            return
        if distance < 0:
            self._append_unique(constraints, seen, LeftOfConstraint(second, first))
            self._append_unique(constraints, seen, RightOfConstraint(first, second))
        else:
            self._append_unique(constraints, seen, LeftOfConstraint(first, second))
            self._append_unique(constraints, seen, RightOfConstraint(second, first))

    def _categories(
        self,
        children: list[Item],
        theme_items: list[Item],
        category_instance: ThemeCategoryInstance | None,
    ) -> list[Category]:
        categories = [Category(name="Children", items=children, type=CategoryType.PERSON)]
        if theme_items and category_instance is not None:
            categories.append(
                Category(
                    name=category_instance.category_id,
                    items=theme_items,
                    type=CategoryType.ATTRIBUTE,
                )
            )
        return categories

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

        if isinstance(constraint, SamePositionConstraint):
            return (
                SamePositionConstraint,
                frozenset((constraint.first, constraint.second)),
            )

        if isinstance(constraint, ExactNumericValueConstraint):
            return (
                ExactNumericValueConstraint,
                constraint.category_id,
                constraint.child,
                constraint.value,
            )

        if isinstance(constraint, NumericDifferenceConstraint):
            return (
                NumericDifferenceConstraint,
                constraint.category_id,
                constraint.greater_child,
                constraint.lesser_child,
                constraint.difference,
            )

        if isinstance(constraint, NumericMultipleConstraint):
            return (
                NumericMultipleConstraint,
                constraint.category_id,
                constraint.multiple_child,
                constraint.base_child,
                constraint.factor,
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
        if isinstance(source, Puzzle):
            return self._copy_metadata(source.metadata)

        if self._theme is None:
            if isinstance(source, PuzzleTemplate):
                return Metadata(title=source.title, theme=source.theme, difficulty=1)
            return None

        category_instance = getattr(self, "_current_category_instance", None)
        selected_ids = () if category_instance is None else category_instance.selected_value_ids
        category_id = "" if category_instance is None else category_instance.category_id
        instance_id = "" if category_instance is None else category_instance.instance_id
        return Metadata(
            title=self._theme.title.en,
            theme="Tennis" if self._theme.id == DEFAULT_THEME_ID else self._theme.title.en,
            difficulty=1,
            theme_id=self._theme.id,
            theme_category_id=category_id,
            theme_category_instance_id=instance_id,
            selected_theme_value_ids=selected_ids,
        )

    def _with_estimated_difficulty(self, puzzle: Puzzle, difficulty: Difficulty) -> Puzzle:
        metadata = self._copy_metadata(puzzle.metadata)
        if metadata is None:
            metadata = Metadata(
                title="Logical Puzzle", theme="General", difficulty=difficulty.metadata_value
            )
        else:
            metadata.difficulty = difficulty.metadata_value

        return Puzzle(
            items=puzzle.items,
            constraints=puzzle.constraints,
            categories=puzzle.categories,
            clues=puzzle.clues,
            metadata=metadata,
            solution=puzzle.solution,
            fixed_positions=dict(puzzle.fixed_positions),
        )

    def _copy_metadata(self, metadata: Metadata | None) -> Metadata | None:
        if metadata is None:
            return None

        return replace(metadata)
