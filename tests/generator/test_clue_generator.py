from __future__ import annotations

import pytest

from logical_puzzle_generator.constraints import (
    AdjacentConstraint,
    FixedPositionConstraint,
    LeftOfConstraint,
    RightOfConstraint,
)
from logical_puzzle_generator.generator import ClueGenerator
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.clue_type import ClueType
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.position import Position
from logical_puzzle_generator.model.puzzle import Puzzle


def test_generate_fixed_position_clue() -> None:
    lara = Item("Lara")

    clues = ClueGenerator().generate(
        [FixedPositionConstraint(lara, Position(1))]
    )

    assert clues == [
        Clue(
            clue_type=ClueType.FIXED_POSITION,
            text="Lara stands at position 1.",
        )
    ]


def test_generate_left_of_clue() -> None:
    lara = Item("Lara")
    mia = Item("Mia")

    clues = ClueGenerator().generate(
        [LeftOfConstraint(lara, mia)]
    )

    assert clues == [
        Clue(
            clue_type=ClueType.LEFT_OF,
            text="Lara stands left of Mia.",
        )
    ]


def test_generate_right_of_clue() -> None:
    lara = Item("Lara")
    mia = Item("Mia")

    clues = ClueGenerator().generate(
        [RightOfConstraint(lara, mia)]
    )

    assert clues == [
        Clue(
            clue_type=ClueType.RIGHT_OF,
            text="Lara stands right of Mia.",
        )
    ]


def test_generate_adjacent_clue() -> None:
    lara = Item("Lara")
    mia = Item("Mia")

    clues = ClueGenerator().generate(
        [AdjacentConstraint(lara, mia)]
    )

    assert clues == [
        Clue(
            clue_type=ClueType.ADJACENT,
            text="Lara stands next to Mia.",
        )
    ]


def test_generate_prevents_duplicate_clues() -> None:
    lara = Item("Lara")
    mia = Item("Mia")

    clues = ClueGenerator().generate(
        [
            LeftOfConstraint(lara, mia),
            LeftOfConstraint(lara, mia),
        ]
    )

    assert clues == [
        Clue(
            clue_type=ClueType.LEFT_OF,
            text="Lara stands left of Mia.",
        )
    ]


def test_generate_preserves_deterministic_order() -> None:
    lara = Item("Lara")
    mia = Item("Mia")
    tim = Item("Tim")
    constraints = [
        AdjacentConstraint(mia, tim),
        FixedPositionConstraint(lara, Position(2)),
        RightOfConstraint(tim, lara),
    ]

    first = ClueGenerator().generate(constraints)
    second = ClueGenerator().generate(constraints)

    assert first == second
    assert [clue.clue_type for clue in first] == [
        ClueType.ADJACENT,
        ClueType.FIXED_POSITION,
        ClueType.RIGHT_OF,
    ]


def test_generate_accepts_puzzle_and_returns_puzzle_with_clues() -> None:
    lara = Item("Lara")
    mia = Item("Mia")
    constraints = [LeftOfConstraint(lara, mia)]
    puzzle = Puzzle(items=[lara, mia], constraints=constraints)

    generated = ClueGenerator().generate(puzzle)

    assert isinstance(generated, Puzzle)
    assert generated.items == [lara, mia]
    assert generated.constraints == constraints
    assert generated.clues == [
        Clue(
            clue_type=ClueType.LEFT_OF,
            text="Lara stands left of Mia.",
        )
    ]


def test_generate_accepts_empty_input() -> None:
    assert ClueGenerator().generate([]) == []


def test_generate_rejects_invalid_input() -> None:
    with pytest.raises(TypeError, match="Constraint instances"):
        ClueGenerator().generate(["not a constraint"])
