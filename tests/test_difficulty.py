from logical_puzzle_generator.difficulty import DifficultyCalculator

def test_difficulty():
    d=DifficultyCalculator()
    assert d.calculate(4)==1
    assert d.calculate(7)==3
    assert d.calculate(12)==5
