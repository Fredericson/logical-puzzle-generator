from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True, slots=True)
class Position:
    """
    Position inside one row.

    Starts with 1.
    """

    index: int

    def __str__(self) -> str:
        return str(self.index)
