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

    theme_id: str = "tennis_training"

    thematic_category_id: str = "training"

    thematic_category_label: str = "Training"

    author: str = "Logical Puzzle Generator"

    version: str = "1.0.0"
