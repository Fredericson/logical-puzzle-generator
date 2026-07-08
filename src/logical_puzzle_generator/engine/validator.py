from __future__ import annotations

from logical_puzzle_generator.engine.solver import Solver


class Validator:

    def __init__(self):

        self._solver = Solver()

    def has_unique_solution(self, puzzle) -> bool:

        result = self._solver.solve(puzzle)

        return result.has_unique_solution

    def is_valid(self, puzzle) -> bool:

        result = self._solver.solve(puzzle)

        return result.has_solution
