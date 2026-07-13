from __future__ import annotations

from dataclasses import dataclass, field

from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.model.clue import Clue
from logical_puzzle_generator.model.category import Category
from logical_puzzle_generator.model.item import Item
from logical_puzzle_generator.model.metadata import Metadata
from logical_puzzle_generator.model.solution import Solution


@dataclass(slots=True)
class Puzzle:
    """
    Core puzzle model used by the solver, validator, generator, and PDF
    renderer.

    A puzzle consists of the items to place, the constraints that define the
    puzzle mathematically, and the human-readable clues shown to the user.
    """

    items: list[Item]

    constraints: list[Constraint]

    categories: list[Category] = field(default_factory=list)

    clues: list[Clue] = field(default_factory=list)

    metadata: Metadata | None = None

    solution: Solution | None = None


