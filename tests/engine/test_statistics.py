from logical_puzzle_generator.engine.statistics import SolverStatistics


def test_statistics():

    statistics = SolverStatistics()

    statistics.assignments_checked = 24

    statistics.valid_assignments = 1

    assert statistics.rejected_assignments == 23
