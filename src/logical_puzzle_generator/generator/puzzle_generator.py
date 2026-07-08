from __future__ import annotations

from logical_puzzle_generator.engine.optimizer import Optimizer
from logical_puzzle_generator.engine.validator import Validator
from logical_puzzle_generator.model.puzzle import Puzzle

from .clue_generator import ClueGenerator
from .solution_generator import SolutionGenerator


class PuzzleGenerator:
    """
    Generates complete logical puzzles.

    Pipeline

        Solution
            ↓
        Clues
            ↓
        Puzzle
            ↓
        Optimizer
            ↓
        Validator
    """

    def __init__(self) -> None:

        self._solution_generator = SolutionGenerator()

        self._clue_generator = ClueGenerator()

        self._optimizer = Optimizer()

        self._validator = Validator()

    def generate(self) -> Puzzle:

        while True:

            solution = self._solution_generator.generate()

            puzzle = self._clue_generator.generate(
                solution
            )

            puzzle = self._optimizer.optimize(
                puzzle
            )

            if self._validator.has_unique_solution(
                puzzle
            ):

                return puzzle
