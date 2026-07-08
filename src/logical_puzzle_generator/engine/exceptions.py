class SolverError(Exception):
    """
    Base solver exception.
    """


class InvalidPuzzleError(SolverError):
    """
    Puzzle definition is invalid.
    """


class NoSolutionError(SolverError):
    """
    No valid solution exists.
    """


class MultipleSolutionsError(SolverError):
    """
    More than one solution exists.
    """
