from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Value:
    """
    Generic value used by categories.

    Examples

    Yellow

    Dog

    Water

    Tennis racket
    """

    value: str

    def __str__(self) -> str:
        return self.value
