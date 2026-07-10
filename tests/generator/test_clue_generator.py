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


def test_generate_fixed_position_clue() -> None:
    lara = Item("Lara")

    constraint = FixedPositionConstraint(lara, Position(1))
    clues = ClueGenerator().generate([constraint])

    assert clues == [
        Clue(
            clue_type=ClueType.FIXED_POSITION,
            text="Lara stands at position 1.",
            constraint=constraint,
        )
    ]


def test_generate_left_of_clue() -> None:
    lara = Item("Lara")
    mia = Item("Mia")

    constraint = LeftOfConstraint(lara, mia)
    clues = ClueGenerator().generate([constraint])

    assert clues == [
        Clue(
            clue_type=ClueType.LEFT_OF,
            text="Lara stands left of Mia.",
            constraint=constraint,
        )
    ]


def test_generate_right_of_clue() -> None:
    lara = Item("Lara")
    mia = Item("Mia")

    constraint = RightOfConstraint(lara, mia)
    clues = ClueGenerator().generate([constraint])

    assert clues == [
        Clue(
            clue_type=ClueType.RIGHT_OF,
            text="Lara stands right of Mia.",
            constraint=constraint,
        )
    ]


def test_generate_adjacent_clue() -> None:
    lara = Item("Lara")
    mia = Item("Mia")

    constraint = AdjacentConstraint(lara, mia)
    clues = ClueGenerator().generate([constraint])

    assert clues == [
        Clue(
            clue_type=ClueType.ADJACENT,
            text="Lara stands next to Mia.",
            constraint=constraint,
        )
    ]


def test_generate_prevents_duplicate_clues() -> None:
    lara = Item("Lara")
    mia = Item("Mia")

    constraint = LeftOfConstraint(lara, mia)
    clues = ClueGenerator().generate(
        [
            constraint,
            LeftOfConstraint(lara, mia),
        ]
    )

    assert clues == [
        Clue(
            clue_type=ClueType.LEFT_OF,
            text="Lara stands left of Mia.",
            constraint=constraint,
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


def test_generate_accepts_empty_input() -> None:
    assert ClueGenerator().generate([]) == []


def test_generate_rejects_invalid_input() -> None:
    with pytest.raises(TypeError, match="Constraint instances"):
        ClueGenerator().generate(["not a constraint"])
