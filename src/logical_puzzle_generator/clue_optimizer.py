from __future__ import annotations

from itertools import combinations

class ClueOptimizer:
    """Find the smallest clue subset with a unique solution."""

    def __init__(self, solver):
        self.solver = solver

    def optimize(self, items, clues):
        for size in range(1, len(clues)+1):
            for subset in combinations(clues, size):
                if self.solver.count(items, list(subset)) == 1:
                    return list(subset)
        return clues
