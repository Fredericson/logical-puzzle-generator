class DifficultyCalculator:
    def calculate(self, clue_count: int) -> int:
        if clue_count <= 4:
            return 1
        if clue_count <= 7:
            return 3
        return 5
