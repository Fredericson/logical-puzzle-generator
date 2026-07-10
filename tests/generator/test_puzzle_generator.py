from __future__ import annotations

import random

import pytest

from logical_puzzle_generator.constraints import (
    AdjacentConstraint,
    FixedPositionConstraint,
    LeftOfConstraint,
    RightOfConstraint,
)
from logical_puzzle_generator.engine.assignment import Assignment
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
    assert len(puzzle.constraints) == len(template.players.items) - 1
    assert len(puzzle.clues) <= len(puzzle.constraints)
    assert len(puzzle.clues) == len({(clue.clue_type, clue.text) for clue in puzzle.clues})
    assert all(constraint.matches(puzzle.solution.assignment) for constraint in puzzle.constraints)
    assert all(isinstance(constraint, LeftOfConstraint) for constraint in puzzle.constraints)


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
