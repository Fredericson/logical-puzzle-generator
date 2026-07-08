from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Clue:
    description: str

@dataclass(frozen=True)
class FixedPosition(Clue):
    item: str
    position: int

@dataclass(frozen=True)
class LeftOf(Clue):
    left: str
    right: str

@dataclass(frozen=True)
class Adjacent(Clue):
    first: str
    second: str
