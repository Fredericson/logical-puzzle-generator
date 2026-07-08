from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from typing import Callable, Iterable


@dataclass(frozen=True)
class Solution:
    assignment: dict[str, int]


class Solver:
    """Simple brute-force solver for 4-position puzzles."""

    def generate_assignments(self, items: list[str]) -> Iterable[Solution]:
        for perm in permutations(range(1, len(items)+1)):
            yield Solution(dict(zip(items, perm)))

    def count_solutions(
        self,
        items: list[str],
        constraints: list[Callable[[dict[str,int]], bool]],
    ) -> int:
        count = 0
        for solution in self.generate_assignments(items):
            if all(c(solution.assignment) for c in constraints):
                count += 1
        return count
