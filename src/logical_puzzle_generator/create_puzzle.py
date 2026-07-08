from .solver import Solver
from .puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.pdf.generator import PdfGenerator

def create_puzzle():
    items=['Lara','Tim','Mia','Noah']
    puzzle=PuzzleGenerator(Solver()).generate(items)
    PdfGenerator().create(puzzle,'output/puzzle.pdf')
    return puzzle

if __name__=='__main__':
    create_puzzle()
