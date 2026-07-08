from logical_puzzle_generator.solution_generator import SolutionGenerator

def test_generate():
    gen=SolutionGenerator()
    a=gen.generate(["A","B","C","D"])
    assert len(a.positions)==4
    assert sorted(a.positions.values())==[1,2,3,4]
