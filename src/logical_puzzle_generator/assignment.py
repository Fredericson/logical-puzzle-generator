from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Assignment:
    positions: dict[str,int]

    def position_of(self,item:str)->int:
        return self.positions[item]
