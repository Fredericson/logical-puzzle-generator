from __future__ import annotations

from logical_puzzle_generator.model.puzzle import Puzzle


class Optimizer:
    """
    Optimizes the set of clues used for a puzzle.

    Version 1.0 intentionally keeps every clue. The class
    already exists so that future versions can minimise the
    clue set without changing the public API.
    """

    def optimize(
        self,
        puzzle: Puzzle,
    ) -> Puzzle:
        """
        Returns an optimized puzzle.

        For version 1.0 no optimization is performed.
        """

        return puzzle
