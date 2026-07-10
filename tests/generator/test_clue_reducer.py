from __future__ import annotations

import pytest

from logical_puzzle_generator.constraints import (
    FixedPositionConstraint,
    LeftOfConstraint,
)
from logical_puzzle_generator.generator import ClueGenerator, ClueReducer
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle


class SequenceValidator:
    def __init__(self, results: list[bool]) -> None:
        self.results = results
        self.puzzles: list[Puzzle] = []

    def has_unique_solution(self, puzzle: Puzzle) -> bool:
        self.puzzles.append(puzzle)
        if not self.results:
            return False
        return self.results.pop(0)


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
    assert reduced.constraints is puzzle.constraints


def test_reduce_preserves_uniqueness_for_each_accepted_removal() -> None:
    puzzle = _puzzle()
    validator = SequenceValidator([True, True])

    reduced = ClueReducer(validator).reduce(puzzle)

    assert reduced.clues == [puzzle.clues[1]]
    assert [len(candidate.clues) for candidate in validator.puzzles] == [1]


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
        constraints=[],
        clues=["not a clue"],  # type: ignore[list-item]
    )

    with pytest.raises(TypeError, match="Clue instances"):
        ClueReducer().reduce(puzzle)
