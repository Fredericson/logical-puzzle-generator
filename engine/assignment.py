from dataclasses import dataclass

@dataclass(frozen=True)
class Assignment:
    positions: dict[str,int]

    def position_of(self,item:str)->int:
        return self.positions[item]

    def items(self):
        return self.positions.keys()
