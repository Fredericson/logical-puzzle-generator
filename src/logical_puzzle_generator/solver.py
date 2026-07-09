from logical_puzzle_generator.engine.solver import Solver as EngineSolver
from logical_puzzle_generator.model.puzzle import Puzzle


class Solver(EngineSolver):
    def count(self, items, constraints) -> int:
        return self.solve(Puzzle(items=list(items), constraints=list(constraints))).solution_count
