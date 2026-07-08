from .solution_generator import SolutionGenerator
from .clue_generator import ClueGenerator

class PuzzleGenerator:

    def __init__(self):
        self.solution_generator=SolutionGenerator()
        self.clue_generator=ClueGenerator()

    def generate(self, items):
        solution=self.solution_generator.generate(items)
        clues=self.clue_generator.generate(solution)
        return solution, clues
