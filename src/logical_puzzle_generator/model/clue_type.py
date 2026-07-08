from __future__ import annotations

from enum import Enum


class ClueType(str, Enum):
    """
    All supported clue types.
    """

    FIXED_POSITION = "fixed_position"

    LEFT_OF = "left_of"

    RIGHT_OF = "right_of"

    ADJACENT = "adjacent"

    NOT_ADJACENT = "not_adjacent"

    BETWEEN = "between"

    NOT_POSITION = "not_position"
