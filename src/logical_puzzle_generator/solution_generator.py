from __future__ import annotations

import random
from .assignment import Assignment

class SolutionGenerator:
    def generate(self, items: list[str]) -> Assignment:
        positions=list(range(1,len(items)+1))
        random.shuffle(positions)
        return Assignment(dict(zip(items, positions)))
