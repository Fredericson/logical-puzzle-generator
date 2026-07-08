from logical_puzzle_generator.solution_generator import SolutionGenerator
def test_solution():
    s=SolutionGenerator().generate(['A','B','C','D'])
    assert sorted(s.positions.values())==[1,2,3,4]
