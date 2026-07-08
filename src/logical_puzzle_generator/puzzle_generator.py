from .solution_generator import SolutionGenerator
from .clue_generator import ClueGenerator
from .clue_optimizer import ClueOptimizer
from .difficulty import DifficultyCalculator
from .validator import Validator
from .puzzle import Puzzle

class PuzzleGenerator:
    def __init__(self, solver):
        self.solver=solver
        self.sg=SolutionGenerator()
        self.cg=ClueGenerator()
        self.opt=ClueOptimizer()
        self.diff=DifficultyCalculator()
        self.validator=Validator()

    def generate(self, items):
        solution=self.sg.generate(items)
        clues=self.cg.generate(solution)
        clues=self.opt.optimize(self.solver,items,clues)
        difficulty=self.diff.calculate(len(clues))
        assert self.validator.unique(items,clues)
        return Puzzle(items,clues,solution,difficulty)
