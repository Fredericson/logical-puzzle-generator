from __future__ import annotations

from dataclasses import dataclass

from logical_puzzle_generator.constraints.base import Constraint

from .clue_type import ClueType


@dataclass(slots=True)
class Clue:
    """
    Human readable clue.

    Example

    Lara stands left of Mia.
    """

    clue_type: ClueType

    text: str

    constraint: Constraint

    difficulty: int = 1

    def __str__(self) -> str:
        return self.text
