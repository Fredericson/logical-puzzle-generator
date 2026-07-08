from __future__ import annotations

from dataclasses import dataclass


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

    def __str__(self) -> str:
        return self.name
