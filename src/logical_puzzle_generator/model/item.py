from __future__ import annotations

from dataclasses import dataclass

from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID


@dataclass(frozen=True, slots=True)
class Item:
    """
    One logical object.

    Examples
    --------
    Lara
    Noah
    Mia
    Tim
    """

    name: str

    category_id: str = CHILDREN_CATEGORY_ID

    def __str__(self) -> str:
        return self.name
