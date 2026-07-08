from dataclasses import dataclass
@dataclass
class Puzzle:
    items:list[str]
    clues:list
    solution:object
    difficulty:int
