from __future__ import annotations

class DifficultyCalculator:
    def calculate(self, clue_count:int)->int:
        if clue_count <= 4:
            return 1
        if clue_count <= 6:
            return 2
        if clue_count <= 8:
            return 3
        if clue_count <= 10:
            return 4
        return 5
