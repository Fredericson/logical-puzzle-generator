def create_puzzle():
    from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
    from logical_puzzle_generator.pdf.generator import PdfGenerator
    from logical_puzzle_generator.solver import Solver

    items = ['Lara', 'Tim', 'Mia', 'Noah']
    puzzle = PuzzleGenerator(Solver()).generate(items)
    PdfGenerator().create(puzzle, 'output/puzzle.pdf')
    return puzzle


if __name__ == '__main__':
    create_puzzle()
