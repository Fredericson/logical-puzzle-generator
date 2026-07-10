from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Metadata:
    """
    Metadata describing one generated puzzle.
    """

    title: str

    theme: str

    difficulty: int

    author: str = "Logical Puzzle Generator"

    version: str = "1.0.0"
