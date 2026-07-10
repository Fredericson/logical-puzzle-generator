from __future__ import annotations

import pytest

from logical_puzzle_generator.constraints import (
    AdjacentConstraint,
    DirectLeftOfConstraint,
    FixedPositionConstraint,
    LeftOfConstraint,
    RightOfConstraint,
)
from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.generator import ClueGenerator, ClueReducer
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.model.solution import Solution


class SequenceValidator:
    def __init__(self, results: list[bool]) -> None:
        self.results = results
        self.puzzles: list[Puzzle] = []

    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        self.puzzles.append(puzzle)
        if not self.results:
            return False
        return self.results.pop(0)


class AlwaysUniqueValidator:
    def __init__(self) -> None:
        self.puzzles: list[Puzzle] = []

    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        self.puzzles.append(puzzle)
        return True


class RecordingDistributionPolicy:
    def __init__(self) -> None:
        self.scored: list[list[object]] = []

    def score(self, constraints):
        constraints = list(constraints)
        self.scored.append(constraints)
        # Prefer candidates retaining an adjacent clue over ordinary right-of only.
        return (1 if any(isinstance(c, AdjacentConstraint) for c in constraints) else 0, 0, 0, 0, 0)


def _puzzle() -> Puzzle:
    a = Item("A")
    b = Item("B")
    constraints = [
        FixedPositionConstraint(a, Position(1)),
        LeftOfConstraint(a, b),
    ]
    return Puzzle(
        items=[a, b],
        constraints=constraints,
        clues=ClueGenerator().generate(constraints),
    )


def test_reduce_removes_clue_when_uniqueness_is_preserved() -> None:
    puzzle = _puzzle()
    validator = SequenceValidator([True, False])

    reduced = ClueReducer(validator).reduce(puzzle)

    assert reduced.clues == [puzzle.clues[1]]
    assert reduced.constraints == [puzzle.constraints[1]]


def test_reduce_preserves_uniqueness_for_each_accepted_removal() -> None:
    puzzle = _puzzle()
    validator = SequenceValidator([True, True])

    reduced = ClueReducer(validator).reduce(puzzle)

    assert reduced.clues == [puzzle.clues[1]]
    assert all(len(candidate.clues) == 1 for candidate in validator.puzzles)


def test_reduce_restores_clue_when_uniqueness_would_be_lost() -> None:
    puzzle = _puzzle()
    validator = SequenceValidator([False, True, False])

    reduced = ClueReducer(validator).reduce(puzzle)

    assert reduced.clues == [puzzle.clues[0]]
    assert [candidate.clues for candidate in validator.puzzles] == [
        [puzzle.clues[1]],
        [puzzle.clues[0]],
    ]


def test_reduce_keeps_already_minimal_puzzle() -> None:
    puzzle = _puzzle()
    validator = SequenceValidator([False, False])

    reduced = ClueReducer(validator).reduce(puzzle)

    assert reduced.clues == puzzle.clues
    assert reduced is not puzzle


def test_reduce_accepts_empty_clue_list() -> None:
    puzzle = _puzzle()
    puzzle.clues = []
    puzzle.constraints = []
    validator = SequenceValidator([])

    reduced = ClueReducer(validator).reduce(puzzle)

    assert reduced.clues == []
    assert validator.puzzles == []


def test_reduce_rejects_invalid_input() -> None:
    with pytest.raises(TypeError, match="Puzzle instance"):
        ClueReducer().reduce("not a puzzle")  # type: ignore[arg-type]


def test_reduce_rejects_invalid_clue_entries() -> None:
    puzzle = Puzzle(
        items=[Item("A")],
        constraints=[FixedPositionConstraint(Item("A"), Position(1))],
        clues=["not a clue"],  # type: ignore[list-item]
    )

    with pytest.raises(TypeError, match="Clue instances"):
        ClueReducer().reduce(puzzle)


def test_reduce_removes_corresponding_constraint_from_candidate() -> None:
    puzzle = _puzzle()
    validator = SequenceValidator([True, False])

    ClueReducer(validator).reduce(puzzle)

    assert validator.puzzles[0].clues == [puzzle.clues[1]]
    assert validator.puzzles[0].constraints == [puzzle.constraints[1]]


def test_reduce_rejects_mismatched_clue_constraint_counts() -> None:
    puzzle = _puzzle()
    puzzle.constraints = puzzle.constraints[:1]

    with pytest.raises(ValueError, match="matching clue and constraint counts"):
        ClueReducer().reduce(puzzle)


def test_reduce_does_not_return_single_non_unique_visible_left_of_clue() -> None:
    emma = Item("Emma")
    aurelia = Item("Aurelia")
    mia = Item("Mia")
    lara = Item("Lara")
    constraints = [
        LeftOfConstraint(emma, aurelia),
        LeftOfConstraint(aurelia, mia),
        LeftOfConstraint(mia, lara),
    ]
    puzzle = Puzzle(
        items=[emma, aurelia, mia, lara],
        constraints=constraints,
        clues=ClueGenerator().generate(constraints),
    )

    reduced = ClueReducer().reduce(puzzle)

    assert len(reduced.clues) > 1
    assert len(reduced.clues) == len(reduced.constraints)
    assert reduced.constraints != [constraints[0]]


def test_reduce_keeps_valid_alternative_clue_to_preserve_four_item_variation() -> None:
    emma = Item("Emma")
    aurelia = Item("Aurelia")
    mia = Item("Mia")
    lara = Item("Lara")
    constraints = [
        FixedPositionConstraint(emma, Position(1)),
        FixedPositionConstraint(lara, Position(4)),
        DirectLeftOfConstraint(aurelia, mia),
    ]
    puzzle = Puzzle(
        items=[emma, aurelia, mia, lara],
        constraints=constraints,
        clues=ClueGenerator(item_count=4).generate(constraints),
        solution=Solution(
            Assignment(
                {
                    emma: Position(1),
                    aurelia: Position(2),
                    mia: Position(3),
                    lara: Position(4),
                }
            )
        ),
    )

    reduced = ClueReducer().reduce(puzzle)

    assert len(reduced.clues) == len(reduced.constraints)
    assert [clue.constraint for clue in reduced.clues] == reduced.constraints
    assert len({_reducer_clue_meaning(clue.text) for clue in reduced.clues}) >= 2


def _reducer_clue_meaning(text: str) -> str:
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


def test_reducer_checks_difficulty_before_distribution_scoring() -> None:
    a, b, c, d = Item("A"), Item("B"), Item("C"), Item("D")
    constraints = [
        FixedPositionConstraint(a, Position(1)),
        FixedPositionConstraint(d, Position(4)),
        LeftOfConstraint(a, b),
    ]
    puzzle = Puzzle(
        items=[a, b, c, d],
        constraints=constraints,
        clues=ClueGenerator(item_count=4).generate(constraints),
        solution=Solution(Assignment({a: Position(1), b: Position(2), c: Position(3), d: Position(4)})),
    )
    policy = RecordingDistributionPolicy()

    reduced = ClueReducer(AlwaysUniqueValidator(), distribution_policy=policy).reduce(puzzle, difficulty="easy")

    assert len([constraint for constraint in reduced.constraints if isinstance(constraint, FixedPositionConstraint)]) == 2
    assert policy.scored
    assert all(
        sum(isinstance(constraint, FixedPositionConstraint) for constraint in scored_constraints) == 2
        for scored_constraints in policy.scored
    )


def test_reducer_uses_distribution_score_only_among_valid_candidates() -> None:
    a, b, c, d = Item("A"), Item("B"), Item("C"), Item("D")
    constraints = [
        FixedPositionConstraint(a, Position(1)),
        FixedPositionConstraint(d, Position(4)),
        RightOfConstraint(c, b),
        AdjacentConstraint(b, c),
    ]
    puzzle = Puzzle(
        items=[a, b, c, d],
        constraints=constraints,
        clues=ClueGenerator(item_count=4).generate(constraints),
        solution=Solution(Assignment({a: Position(1), b: Position(2), c: Position(3), d: Position(4)})),
    )

    reduced = ClueReducer(
        AlwaysUniqueValidator(),
        distribution_policy=RecordingDistributionPolicy(),
    ).reduce(puzzle, difficulty="easy")

    assert any(isinstance(constraint, AdjacentConstraint) for constraint in reduced.constraints)
    assert len(reduced.clues) == len(reduced.constraints)
    assert [clue.constraint for clue in reduced.clues] == reduced.constraints
