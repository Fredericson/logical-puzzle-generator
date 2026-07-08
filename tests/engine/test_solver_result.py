from logical_puzzle_generator.engine.solver_result import SolverResult


def test_empty_result():

    result = SolverResult()

    assert result.solution_count == 0

    assert result.has_solution is False

    assert result.has_unique_solution is False


def test_unique_solution():

    result = SolverResult()

    result.solutions.append(object())

    assert result.solution_count == 1

    assert result.has_solution

    assert result.has_unique_solution
