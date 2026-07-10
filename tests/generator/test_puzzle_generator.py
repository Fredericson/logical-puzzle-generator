from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.constraints import (
    AdjacentConstraint,
    FixedPositionConstraint,
    LeftOfConstraint,
)
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.engine.solver import Solver
from logical_puzzle_generator.generator import ClueGenerator
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.generator.puzzle_template import PuzzleTemplate
from logical_puzzle_generator.model.category import Category
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution
from logical_puzzle_generator.themes.tennis import create_template


class RejectThenAcceptValidator:
    def __init__(self) -> None:
        self.calls = 0

    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        self.calls += 1
        return self.calls > 1


class IdentityClueReducer:
    def reduce(self, puzzle: Puzzle) -> Puzzle:
        return puzzle


class RecordingValidator:
    def __init__(self) -> None:
        self.puzzles: list[Puzzle] = []

    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        self.puzzles.append(puzzle)
        return True


def test_generate_returns_complete_unique_puzzle() -> None:
    template = create_template()

    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(template)

    assert puzzle.items == template.players.items
    assert puzzle.solution is not None
    assert puzzle.metadata is not None
    assert puzzle.metadata.title == template.title
    assert puzzle.metadata.theme == template.theme
    assert len(puzzle.clues) <= len(puzzle.constraints)
    assert len(puzzle.clues) == len({(clue.clue_type, clue.text) for clue in puzzle.clues})
    assert all(constraint.matches(puzzle.solution.assignment) for constraint in puzzle.constraints)
    assert len({clue.clue_type for clue in puzzle.clues}) >= 2


def test_generate_validates_uniqueness() -> None:
    validator = RecordingValidator()

    puzzle = PuzzleGenerator(
        random_source=random.Random(11),
        validator=validator,
        clue_reducer=IdentityClueReducer(),
    ).generate(create_template())

    assert validator.puzzles == [puzzle, puzzle]


def test_generate_retries_when_puzzle_is_not_unique() -> None:
    validator = RejectThenAcceptValidator()

    puzzle = PuzzleGenerator(
        random_source=random.Random(13),
        validator=validator,
        clue_reducer=IdentityClueReducer(),
        max_attempts=3,
    ).generate(create_template())

    assert validator.calls == 3
    assert puzzle.solution is not None


def test_generate_is_deterministic_with_seeded_random_source() -> None:
    template = create_template()

    first = PuzzleGenerator(random_source=random.Random(23)).generate(template)
    second = PuzzleGenerator(random_source=random.Random(23)).generate(template)

    assert first.solution is not None
    assert second.solution is not None
    assert first.solution.positions == second.solution.positions
    assert [constraint.description for constraint in first.constraints] == [
        constraint.description for constraint in second.constraints
    ]
    assert [clue.text for clue in first.clues] == [clue.text for clue in second.clues]


def test_generate_rejects_invalid_input() -> None:
    with pytest.raises(TypeError, match="model.Item"):
        PuzzleGenerator(random_source=random.Random(1)).generate(["A", "B"])


def test_generate_rejects_empty_template() -> None:
    template = PuzzleTemplate(
        title="Empty",
        theme="Test",
        categories=[Category("Players", [])],
    )

    with pytest.raises(ValueError, match="at least one item"):
        PuzzleGenerator(random_source=random.Random(1)).generate(template)


def test_generate_fails_after_max_attempts() -> None:
    class RejectingValidator:
        def __init__(self) -> None:
            self.calls = 0

        def has_unique_solution(self, puzzle: Puzzle) -> bool:
            self.calls += 1
            return False

    validator = RejectingValidator()

    with pytest.raises(RuntimeError, match="Unable to generate"):
        PuzzleGenerator(
            random_source=random.Random(1),
            validator=validator,
            max_attempts=2,
        ).generate(create_template())

    assert validator.calls == 2


def test_generate_supports_single_item_with_fixed_position_constraint() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(1)).generate([Item("Solo")])

    assert len(puzzle.constraints) == 1
    assert isinstance(puzzle.constraints[0], FixedPositionConstraint)
    assert puzzle.solution is not None


def test_generate_rejects_duplicate_items() -> None:
    item = Item("A")

    with pytest.raises(ValueError, match="unique items"):
        PuzzleGenerator(random_source=random.Random(1)).generate([item, item])


class AlwaysUniqueValidator:
    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        return True


class EmptyClueGenerator:
    def generate(self, constraints: object) -> list[Clue]:
        return []


class InvalidSolutionGenerator:
    def generate(self, source: object) -> object:
        return "not a solution"


class EmptyClueReducer:
    def reduce(self, puzzle: Puzzle) -> Puzzle:
        return Puzzle(
            items=puzzle.items,
            constraints=puzzle.constraints,
            clues=[],
            metadata=puzzle.metadata,
            solution=puzzle.solution,
        )


class NonUniqueAfterReductionValidator:
    def __init__(self) -> None:
        self.calls = 0

    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        self.calls += 1
        return self.calls % 2 == 1


class RecordingSolutionGenerator:
    def __init__(self) -> None:
        self.generated_positions: list[tuple[int, ...]] = []

    def generate(self, source: object) -> Solution:
        items = list(source)  # type: ignore[arg-type]
        positions = [Position(index) for index in range(1, len(items) + 1)]
        solution = Solution(Assignment(dict(zip(items, positions, strict=True))))
        self.generated_positions.append(
            tuple(solution.assignment.position_of(item).index for item in items)
        )
        return solution


def test_generate_rejects_invalid_generated_solution_with_clear_message() -> None:
    with pytest.raises(RuntimeError, match="solution generator did not return a Solution"):
        PuzzleGenerator(
            solution_generator=InvalidSolutionGenerator(),
            max_attempts=2,
        ).generate(create_template())


def test_generate_rejects_missing_clues_with_clear_message() -> None:
    with pytest.raises(RuntimeError, match="clue generation produced no clues"):
        PuzzleGenerator(
            random_source=random.Random(1),
            clue_generator=EmptyClueGenerator(),
            validator=AlwaysUniqueValidator(),
            max_attempts=1,
        ).generate(create_template())


def test_generate_rejects_invalid_clue_reduction_with_clear_message() -> None:
    with pytest.raises(RuntimeError, match="clue reduction returned invalid clues"):
        PuzzleGenerator(
            random_source=random.Random(1),
            validator=AlwaysUniqueValidator(),
            clue_reducer=EmptyClueReducer(),
            max_attempts=1,
        ).generate(create_template())


def test_generate_retries_when_reduced_puzzle_is_not_unique() -> None:
    validator = NonUniqueAfterReductionValidator()

    with pytest.raises(RuntimeError, match="reduced clue set is not uniquely solvable"):
        PuzzleGenerator(
            random_source=random.Random(1),
            validator=validator,
            clue_reducer=IdentityClueReducer(),
            max_attempts=2,
        ).generate(create_template())

    assert validator.calls == 4


def test_generate_retry_sequence_is_deterministic() -> None:
    class RejectingValidator:
        def has_unique_solution(self, puzzle: Puzzle) -> bool:
            return False

    items = [Item("A"), Item("B")]
    first_generator = RecordingSolutionGenerator()
    second_generator = RecordingSolutionGenerator()

    with pytest.raises(RuntimeError, match="not uniquely solvable before clue reduction"):
        PuzzleGenerator(
            solution_generator=first_generator,
            validator=RejectingValidator(),
            max_attempts=3,
        ).generate(items)

    with pytest.raises(RuntimeError, match="not uniquely solvable before clue reduction"):
        PuzzleGenerator(
            solution_generator=second_generator,
            validator=RejectingValidator(),
            max_attempts=3,
        ).generate(items)

    assert first_generator.generated_positions == second_generator.generated_positions
    assert first_generator.generated_positions == [(1, 2), (1, 2), (1, 2)]


def test_generate_includes_attempt_count_in_exhaustion_message() -> None:
    with pytest.raises(RuntimeError, match="within 2 attempts.*Last failure: attempt 2"):
        PuzzleGenerator(
            random_source=random.Random(1),
            clue_generator=EmptyClueGenerator(),
            max_attempts=2,
        ).generate(create_template())


def test_four_item_left_of_single_visible_clue_is_not_unique() -> None:
    items = [Item("Emma"), Item("Aurelia"), Item("Mia"), Item("Lara")]
    constraint = LeftOfConstraint(items[0], items[1])
    puzzle = Puzzle(
        items=items,
        constraints=[constraint],
        clues=ClueGenerator().generate([constraint]),
    )

    result = Solver().solve(puzzle, stop_after=2)

    assert not result.has_unique_solution
    assert result.solution_count == 2


def test_generated_reduced_puzzle_solves_to_target_solution_from_visible_constraints() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())

    assert puzzle.solution is not None
    assert len(puzzle.clues) == len(puzzle.constraints)
    assert [clue.constraint for clue in puzzle.clues] == puzzle.constraints

    result = Solver().solve(puzzle, stop_after=2)

    assert result.has_unique_solution
    assert result.solutions[0] == puzzle.solution.assignment


def test_generated_four_item_puzzle_has_varied_visible_clue_types() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(7)).generate(create_template())

    assert len(puzzle.items) == 4
    assert len({clue.clue_type for clue in puzzle.clues}) >= 2
    assert any("directly" in clue.text or "far" in clue.text for clue in puzzle.clues)


def test_seeded_generation_produces_deterministic_clue_types_and_text() -> None:
    template = create_template()

    first = PuzzleGenerator(random_source=random.Random(101)).generate(template)
    second = PuzzleGenerator(random_source=random.Random(101)).generate(template)

    assert [(clue.clue_type, clue.text) for clue in first.clues] == [
        (clue.clue_type, clue.text) for clue in second.clues
    ]


def test_every_generated_clue_constraint_matches_target_and_no_hidden_constraints() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(11)).generate(create_template())

    assert len(puzzle.clues) == len(puzzle.constraints)
    assert [clue.constraint for clue in puzzle.clues] == puzzle.constraints
    assert all(clue.constraint.matches(puzzle.solution.assignment) for clue in puzzle.clues)


def test_generated_visible_puzzle_remains_uniquely_solvable_to_target() -> None:
    puzzle = PuzzleGenerator(random_source=random.Random(17)).generate(create_template())

    result = Solver().solve(puzzle, stop_after=2)

    assert result.has_unique_solution
    assert result.solutions[0] == puzzle.solution.assignment


def test_multiple_seeded_four_item_puzzles_keep_visible_invariants_and_variety() -> None:
    adjacent_seen = False

    for seed in range(1, 16):
        puzzle = PuzzleGenerator(random_source=random.Random(seed)).generate(create_template())
        result = Solver().solve(puzzle, stop_after=2)

        assert result.has_unique_solution, seed
        assert result.solutions[0] == puzzle.solution.assignment
        assert len(puzzle.clues) == len(puzzle.constraints)
        assert [clue.constraint for clue in puzzle.clues] == puzzle.constraints
        assert len({_visible_clue_meaning(clue.text) for clue in puzzle.clues}) >= 2

        adjacent_seen = adjacent_seen or any(
            isinstance(constraint, AdjacentConstraint) for constraint in puzzle.constraints
        )

    assert adjacent_seen


def _visible_clue_meaning(text: str) -> str:
    if "far left" in text:
        return "far_left"
    if "far right" in text:
        return "far_right"
    if "directly left" in text:
        return "directly_left_of"
    if "directly right" in text:
        return "directly_right_of"
    if "left of" in text:
        return "left_of"
    if "right of" in text:
        return "right_of"
    if "next to" in text:
        return "next_to"
    return text
