from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(slots=True)
class GeneratedSolution:
    positions: dict[object, int]


class SolutionGenerator:
    def generate(self, items):
        positions = list(range(1, len(items) + 1))
        random.shuffle(positions)
        return GeneratedSolution(dict(zip(items, positions)))
