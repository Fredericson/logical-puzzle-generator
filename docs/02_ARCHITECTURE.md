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
  localization.py Language enum and translation catalog
  clue_text_renderer.py Localized clue wording
  themes/         Reusable puzzle templates
  create_puzzle.py Tennis PDF entry point
```

Dependencies flow inward to the model and engine. The engine does not depend on generator, PDF, or themes. PDF depends on model objects only for rendering. Localization and clue text rendering are presentation services. Themes provide data only.

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

All constraints inherit from `Constraint` and implement `matches(assignment)`. Implemented Version 1.0 positional constraints are:

- `FixedPositionConstraint(item, position)`
  - `Position(1)` renders as a far-left clue.
  - `Position(item_count)` renders as a far-right clue.
- `DirectLeftOfConstraint(left, right)`
  - means the left item is immediately left of the right item.
- `LeftOfConstraint(left, right)`
  - means the left item is somewhere left of the right item.
- `DirectRightOfConstraint(right, left)`
  - means the right item is immediately right of the left item.
- `RightOfConstraint(right, left)`
  - means the right item is somewhere right of the left item.
- `AdjacentConstraint(first, second)`
  - means the two items are next to each other, but the direction is unknown.

Each constraint exposes a legacy human-readable `description` for compatibility, but descriptions are not the localization mechanism. Constraint classes do not know about solving, PDF rendering, clue reduction, localization, or other constraints. Every visible `Clue` owns exactly one corresponding `Constraint`; the generator and reducer preserve this one-to-one relationship so the puzzle shown to the player is the same puzzle validated by the engine.

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

Current derivation sorts the generated solution by position and creates a varied set of true positional constraints. It may include far-left and far-right fixed-position constraints, direct-left/direct-right or undirected adjacent constraints for neighboring ordered items, and ordinary left-of/right-of constraints for longer-range relationships. For a one-item puzzle it creates a `FixedPositionConstraint` instead. Derived constraints are de-duplicated and verified against the generated solution.

### `ClueGenerator`

Converts supplied constraint instances into deterministic English `Clue` objects for backward compatibility. It supports far-left, far-right, directly-left-of, left-of, directly-right-of, right-of, and next-to wording. It does not create constraints, solve puzzles, reduce clues, or randomize output.

### `ClueReducer`

Attempts a deterministic remove-and-validate pass over human-readable clues. It removes a `Clue` and its corresponding `Constraint` together, never validates hidden constraints, and only accepts removals when `Validator.has_unique_solution()` remains true for the visible constraints that remain. For normal four-item puzzles it preserves at least two visible clue meanings when a varied valid alternative is available.

### `PuzzleGenerator`

Coordinates the complete pipeline and validates every stage. It accepts optional injected `SolutionGenerator`, `ClueGenerator`, `Validator`, and `ClueReducer` instances for tests and compatibility. It retries up to `max_attempts` and raises `RuntimeError` with the last failure when generation cannot produce a valid uniquely solvable puzzle.

Pipeline:

```text
Source template/items
        ↓
SolutionGenerator
        ↓
Constraint derivation
        ↓
ClueGenerator
        ↓
ClueReducer
        ↓
Validator
        ↓
Quality selection
        ↓
PDF Generator
```

During generation, `PuzzleGenerator` assembles multiple valid candidate puzzles when possible. Each candidate is validated for uniqueness before clue reduction, reduced with visible clues and matching constraints removed together, and validated again after reduction. Uniqueness is always validated against the constraints that correspond to visible clues; hidden constraints are forbidden.

After collecting valid candidates, `PuzzleGenerator` scores each candidate with a deterministic internal quality heuristic and returns the highest-scoring puzzle. Multiple candidates are generated because the first uniquely solvable clue set can be mathematically valid but repetitive for a human player; comparing several valid reduced alternatives lets the generator prefer a more varied visible clue set without changing solver, reducer, or public API behavior.

The quality score is based on constraint type and `ClueType`, not rendered English text, so scoring stays independent from localisation, clue wording, and PDF presentation. Its weights are intentionally simple and documented in code: clue-meaning variety receives the largest reward because avoiding repetition is the main quality goal; endpoint clues receive a smaller reward because they give useful starting anchors; adjacent and direct-left/direct-right relationship clues receive medium rewards because they create interesting relational deductions; duplicate meanings and a dominant single meaning receive penalties to keep the distribution balanced. The heuristic is not a difficulty estimate.

The number of valid candidates considered is controlled by the internal `QUALITY_CANDIDATE_COUNT` constant. Seeded `random.Random` inputs remain deterministic because candidate generation consumes randomness in a stable sequence, every valid candidate is scored with a pure deterministic function, and ties are resolved by the stable order of the generated candidate list.

## 7. Localization and PDF packages

`Language` defines supported presentation languages: `Language.ENGLISH` (`en`) and `Language.GERMAN` (`de`). `TranslationCatalog` centralizes PDF headings, labels, CLI-facing output labels, and metadata-title translations. `ClueTextRenderer` renders clue wording from each clue's linked constraint in the selected language. This keeps German wording out of constraints, solver, validator, and generator logic. English remains the default and uses stored `Clue.text` for backward compatibility.

German PDF output uses Swiss-compatible spelling without `ß`, for example `Tennistraining`, `Thema`, `Schwierigkeit`, `Hinweise`, `Lösungsraster`, `Antwort`, and `Lösung`.

## 8. PDF package

`TextRenderer` renders clues, solution rows, and item names as strings. It validates that rendered text is human-readable.

`PdfGenerator` writes ReportLab PDFs:

- `create_puzzle_pdf(puzzle, filename)` writes the unsolved puzzle PDF.
- `create_solution_pdf(puzzle, filename)` writes the solved PDF.
- `create(puzzle, filename)` is a backward-compatible wrapper for `create_puzzle_pdf()`.

PDF generation is presentation-only. It must not derive constraints, solve puzzles, or alter puzzle data.

## 9. Theme and entry-point flow

`themes.tennis.create_template()` returns the built-in Tennis `PuzzleTemplate`.

`create_puzzle.create_puzzle()` generates that template and writes both default PDFs. It accepts `language="en"`, `language="de"`, or a `Language` value; English is the default:

```text
output/puzzle_3.pdf
output/puzzle_3_solution.pdf
```

## 10. Data flow

```text
Theme/PuzzleTemplate or Item iterable
        ↓
SolutionGenerator
        ↓
Constraint derivation
        ↓
ClueGenerator
        ↓
ClueReducer
        ↓
Validator → Solver → AssignmentIterator
        ↓
Quality selection
        ↓
PdfGenerator / TextRenderer / ClueTextRenderer / TranslationCatalog
```

## 11. Architecture preservation policy

Stable boundaries:

- Model objects remain behavior-light.
- Constraints remain independent `matches()` implementations.
- Solver remains a generic brute-force engine.
- Validator remains the uniqueness boundary.
- Generator orchestration stays in `PuzzleGenerator`.
- PDF remains presentation-only.
- Localization remains presentation-only and must not change generation or solving semantics.

Significant changes to these boundaries require an ADR update.
