from __future__ import annotations

import random

from logical_puzzle_generator.engine.assignment import Assignment
from logical_puzzle_generator.model.solution import Solution


class SolutionGenerator:
    def generate(self, items):
        positions = list(range(1, len(items) + 1))
        random.shuffle(positions)
        return Solution(Assignment(dict(zip(items, positions))))
