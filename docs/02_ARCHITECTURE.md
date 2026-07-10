# Logical Puzzle Generator Architecture

This document describes the current Version 1.0 architecture.

## 1. Version 1.0 boundary

Version 1.0 generates ordering puzzles over one active item category. A generated `Solution` is a complete mapping from each active item to a `Position`. The public Tennis template includes multiple thematic categories, but the generator uses the first category as the active players/items category.

Out of scope for Version 1.0: multi-category relationship solving, larger grids, JSON export, batch generation, GUI/web apps, REST APIs, and advanced difficulty modeling.

## 2. Package structure

```text
logical_puzzle_generator/
  model/          Domain data objects
  constraints/    Mathematical rules over assignments
  engine/         Brute-force solving and validation
  generator/      Puzzle generation orchestration
  pdf/            Presentation-only PDF rendering
  themes/         Reusable puzzle templates
  create_puzzle.py Tennis PDF entry point
```

Dependencies flow inward to the model and engine. The engine does not depend on generator, PDF, or themes. PDF depends on model objects only for rendering. Themes provide data only.

## 3. Model package

`model` contains domain objects:

- `Item`: immutable named puzzle object.
- `Position`: immutable 1-based ordered position.
- `Category` and `CategoryType`: named item groups for templates.
- `Clue` and `ClueType`: human-readable clue model and clue classification.
- `Metadata`: title, theme, difficulty, author, and version information.
- `Puzzle`: items, constraints, clues, optional metadata, and optional solution.
- `Solution`: generated assignment plus solver iteration metadata.

Model objects should remain lightweight. Solver, generator, and PDF behavior belongs outside the model package.

## 4. Constraints package

All constraints inherit from `Constraint` and implement `matches(assignment)`. Implemented Version 1.0 constraints are:

- `FixedPositionConstraint(item, position)`
- `LeftOfConstraint(left, right)`
- `RightOfConstraint(right, left)`
- `AdjacentConstraint(first, second)`

Each constraint exposes a human-readable `description`. Constraint classes do not know about solving, PDF rendering, clue reduction, or other constraints.

## 5. Engine package

The engine is the mathematical core:

- `Assignment` maps each `Item` to a `Position`.
- `AssignmentIterator` enumerates every permutation of positions for a list of items.
- `Solver` checks each assignment against all puzzle constraints and returns `SolverResult`.
- `SolverResult` exposes solution count, first solution, and uniqueness helpers.
- `SolverStatistics` records assignments checked, valid assignments, rejected assignments, and elapsed time.
- `Validator` wraps `Solver` and exposes `is_valid()` and `has_unique_solution()`.
- `Optimizer` is a compatibility boundary for future optimization; in Version 1.0 it returns the puzzle unchanged.

The solver is intentionally brute force. For four active items this is simple, deterministic, and fast enough.

## 6. Generator package

### `PuzzleTemplate`

Defines a title, theme, and categories. `players` returns the first category, which is the active source category in Version 1.0.

### `SolutionGenerator`

Creates a random one-to-one mapping from active items to positions. It accepts a `PuzzleTemplate`, `Puzzle`, or iterable of `Item` objects. A caller may inject `random.Random` for deterministic generation.

### Internal constraint derivation

`PuzzleGenerator` owns constraint derivation as a private implementation detail. There is no public `ConstraintGenerator` in Version 1.0.

Current derivation sorts the generated solution by position and creates enough ordered `LeftOfConstraint` instances between neighboring ordered items to uniquely determine that order. For a one-item puzzle it creates a `FixedPositionConstraint` instead. Derived constraints are de-duplicated and verified against the generated solution.

### `ClueGenerator`

Converts supplied constraint instances into deterministic `Clue` objects. It supports fixed-position, left-of, right-of, and adjacent constraints. It does not create constraints, solve puzzles, reduce clues, or randomize output.

### `ClueReducer`

Attempts a deterministic remove-and-validate pass over human-readable clues. It never changes the puzzle's items, mathematical constraints, metadata, or solution. It stops before returning an empty clue set and only accepts removals when `Validator.has_unique_solution()` remains true.

### `PuzzleGenerator`

Coordinates the complete pipeline and validates every stage. It accepts optional injected `SolutionGenerator`, `ClueGenerator`, `Validator`, and `ClueReducer` instances for tests and compatibility. It retries up to `max_attempts` and raises `RuntimeError` with the last failure when generation cannot produce a valid uniquely solvable puzzle.

Pipeline:

```text
source
  ↓
extract and validate items
  ↓
generate Solution
  ↓
derive constraints internally
  ↓
generate Clue objects
  ↓
assemble Puzzle
  ↓
validate unique solution
  ↓
reduce clues
  ↓
validate reduced puzzle still has a unique solution
  ↓
return Puzzle
```

## 7. PDF package

`TextRenderer` renders clues, solution rows, and item names as strings. It validates that rendered text is human-readable.

`PdfGenerator` writes ReportLab PDFs:

- `create_puzzle_pdf(puzzle, filename)` writes the unsolved puzzle PDF.
- `create_solution_pdf(puzzle, filename)` writes the solved PDF.
- `create(puzzle, filename)` is a backward-compatible wrapper for `create_puzzle_pdf()`.

PDF generation is presentation-only. It must not derive constraints, solve puzzles, or alter puzzle data.

## 8. Theme and entry-point flow

`themes.tennis.create_template()` returns the built-in Tennis `PuzzleTemplate`.

`create_puzzle.create_puzzle()` generates that template and writes both default PDFs:

```text
output/puzzle_3.pdf
output/puzzle_3_solution.pdf
```

## 9. Data flow

```text
Theme/PuzzleTemplate or Item iterable
        ↓
SolutionGenerator
        ↓
Solution + Assignment
        ↓
PuzzleGenerator private constraint derivation
        ↓
Constraint list
        ↓
ClueGenerator
        ↓
Clue list
        ↓
Puzzle
        ↓
Validator → Solver → AssignmentIterator
        ↓
ClueReducer
        ↓
Validator → Solver
        ↓
PdfGenerator / TextRenderer
```

## 10. Architecture preservation policy

Stable boundaries:

- Model objects remain behavior-light.
- Constraints remain independent `matches()` implementations.
- Solver remains a generic brute-force engine.
- Validator remains the uniqueness boundary.
- Generator orchestration stays in `PuzzleGenerator`.
- PDF remains presentation-only.

Significant changes to these boundaries require an ADR update.
