# Logical Puzzle Generator

Logical Puzzle Generator creates small, printable Einstein-style ordering puzzles and verifies them mathematically before returning them. Version 1.0 focuses on a stable 4-item puzzle pipeline: generate a solution, derive constraints, apply a deterministic constraint distribution policy for clue variety, convert them to clues, validate uniqueness, reduce redundant clues, and render child-friendly A4 puzzle and solution PDFs.

## Version 1.0 capabilities

- Generate a complete one-to-one assignment of puzzle items to positions.
- Derive internal mathematical constraints from the generated solution.
- Convert supported constraints into human-readable English clues and render localized clue text for PDFs.
- Validate that a puzzle has exactly one solution using the brute-force solver.
- Reduce unnecessary clues while preserving unique solvability and at least one clue.
- Generate printable A4 puzzle and solution PDFs with ReportLab in English (`en`, default) or German (`de`).
- Render the Tennis puzzle as a horizontal child-friendly lineup of four anonymous vector girls, empty handwriting boxes, and left-to-right position numbers.
- Provide a Tennis theme and a convenience entry point that writes PDFs to `output/`.

Version 1.0 is intentionally limited to ordering puzzles over one active category of items. Additional category relationships, richer clue types, JSON export, batch generation, GUI/web interfaces, and larger puzzle sizes are Version 2+ work.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pip install -e .
```

The package requires Python 3.11 or newer.

## Run tests and checks

```bash
pytest
ruff check src tests
black --check src tests
mypy src
```

## Generate a puzzle and PDFs

Use the built-in entry point to generate the Tennis puzzle PDFs:

```bash
python -m logical_puzzle_generator.create_puzzle
python -m logical_puzzle_generator.create_puzzle --number 3 --language en
python -m logical_puzzle_generator.create_puzzle --number 3 --language de
python -m logical_puzzle_generator.create_puzzle --number 3 --language de --difficulty easy
```

By default this writes:

- `output/puzzle_3.pdf`
- `output/puzzle_3_solution.pdf`

You can also call the public API directly:

```python
from logical_puzzle_generator.create_puzzle import create_puzzle

puzzle = create_puzzle(
    number=3,
    puzzle_path="output/puzzle.pdf",
    solution_path="output/solution.pdf",
    language="de",
    difficulty="easy",  # use None or omit to choose randomly
)
print(puzzle.metadata.title)
```

To generate a puzzle without writing PDFs:

```python
from logical_puzzle_generator.generator import PuzzleGenerator
from logical_puzzle_generator.themes.tennis import create_template

puzzle = PuzzleGenerator().generate(create_template())
print([clue.text for clue in puzzle.clues])
```

The puzzle PDF uses A4 portrait output. Its Tennis layout shows four anonymous vector girls from left to right, one empty writable name box per position, position numbers 1-4, localized clues, and a separate available-names list. The solution PDF reuses the same lineup and fills the boxes from `puzzle.solution.assignment` without solving again.

To render PDFs for an existing puzzle:

```python
from logical_puzzle_generator.pdf.generator import PdfGenerator

pdf = PdfGenerator(language="en")
pdf.create_puzzle_pdf(puzzle, "output/puzzle.pdf")
pdf.create_solution_pdf(puzzle, "output/solution.pdf")
```

## Project structure

```text
src/logical_puzzle_generator/
  model/          Domain models: Item, Position, Puzzle, Solution, Clue, Metadata, Category
  constraints/    Constraint classes used by the solver and clue generator
  engine/         Assignment iteration, brute-force solver, statistics, validation, optimizer stub
  generator/      SolutionGenerator, FixedPositionGenerator, ConstraintDistributionPolicy, ClueGenerator, ClueReducer, PuzzleGenerator, PuzzleTemplate
  pdf/            TextRenderer, vector lineup renderers, and PdfGenerator presentation layer
  localization.py Language enum and translation catalog
  clue_text_renderer.py Localized clue wording for presentation
  themes/         Built-in puzzle templates, currently Tennis
  create_puzzle.py Convenience script for generating the Tennis PDFs

tests/            Pytest coverage for model, engine, generator, and PDF behavior
docs/             Version 1.0 project documentation and AI workflow guidance
examples/         Placeholder for generated example artifacts and future examples
```

## Documentation

Start with `docs/README.md`. The main documents are:

- `docs/01_AI_DEVELOPMENT_SPEC.md`
- `docs/02_ARCHITECTURE.md`
- `docs/03_CONTRIBUTING_AI.md`
- `docs/04_ROADMAP.md`
- `docs/05_DECISIONS.md`
- `docs/06_PROMPTS.md`

## Language support

English is the default for backward compatibility. German can be selected with `--language de`, `create_puzzle(..., language="de")`, or `PdfGenerator(language="de")`. Public callers may also use `Language.GERMAN`. Unsupported language values are rejected instead of silently falling back. Localization is presentation-only: solver, validator, constraints, and generation semantics remain language-independent. Difficulty is selected at generation time (omit it or pass `None` to choose randomly) and is determined only by the number of final visible `FixedPositionConstraint` clues: Easy has exactly two, Medium has exactly one, and Hard has zero. The numeric metadata remains `1`/`2`/`3`; PDFs only render localized labels (`Easy`/`Medium`/`Hard` or `Leicht`/`Mittel`/`Schwierig`).

### Selectable difficulty

Generated puzzles choose a random difficulty when `--difficulty` is omitted or `create_puzzle(..., difficulty=None)` is used. A specific level may be requested with `--difficulty easy`, `--difficulty medium`, or `--difficulty hard`, or programmatically with `create_puzzle(..., difficulty="easy")` / `Difficulty.EASY`. Difficulty is the final visible fixed-position clue count only: Easy `== 2`, Medium `== 1`, Hard `== 0`. Direct-left, direct-right, adjacent, left-of, and right-of clues do not count as fixed-position clues. Generation uses the injected random source to choose both anchored children and anchored positions, builds a solution consistent with those choices, and retries until the reduced, uniquely solvable visible clue set matches the requested level; PDF localization only maps stored `1/2/3` metadata to labels.


### Clue variety policy

`ConstraintDistributionPolicy` analyzes generated constraints before clue text is created. It receives only neutral distribution context, such as the required fixed-position count, and does not understand Easy, Medium, or Hard. Its rule-based acceptance rejects obviously repetitive four-item relation mixes, while its small deterministic comparison score ranks relation variety by distinct relation types, repeats, dominance, adjacency, and direct-neighbour clues. This is a quality optimization only: `DifficultyPolicy` owns difficulty, solver and validator uniqueness checks remain the correctness authority, and no new clue or constraint types are introduced. The reducer uses the same score only as a tie-breaker after difficulty preservation and uniqueness have already been checked.
