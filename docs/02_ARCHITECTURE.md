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
  pdf/            Presentation-only text, vector lineup, polished worksheet layout, and PDF rendering
  localization.py Language enum and translation catalog
  clue_text_renderer.py Localized clue wording renderer
  template_catalog.py Central localized clue wording templates
  themes/         Reusable puzzle templates
  create_puzzle.py Tennis PDF entry point
```

Dependencies flow inward to the model and engine. The engine does not depend on generator, PDF, or themes. PDF depends on model objects only for rendering. Localization and clue text rendering are presentation services. Themes provide data only. Version 1 presentation polish stays inside this boundary: it changes worksheet spacing, typography, clue indentation, and vector lineup geometry without changing generated constraints, clues, difficulty, metadata, localization semantics, or solving.

## 3. Model package

`model` contains domain objects:

- `Item`: immutable named puzzle object.
- `Position`: immutable 1-based ordered position.
- `Category` and `CategoryType`: named item groups for templates.
- `Clue` and `ClueType`: human-readable clue model and clue classification.
- `Metadata`: title, theme, numeric difficulty, author, and version information. The numeric difficulty is selected at generation time and stored after classifying final visible constraints by `FixedPositionConstraint` count; child-facing labels are a PDF localization concern.
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
  - means the left item is somewhere left of the right item; generated target-solution pairs must be non-adjacent (distance >= 2).
- `DirectRightOfConstraint(right, left)`
  - means the right item is immediately right of the left item.
- `RightOfConstraint(right, left)`
  - means the right item is somewhere right of the left item; generated target-solution pairs must be non-adjacent (distance >= 2).
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

### `FixedPositionGenerator`

Constructs the selected difficulty anchors before relational constraints exist. It determines the required fixed count (Easy 2, Medium 1, Hard 0), randomly selects distinct items and distinct positions with the injected `random.Random`, pairs those fixed assignments, fills remaining items and positions one-to-one, and returns the mandatory `FixedPositionConstraint` instances together with the complete target `Solution`. It does not generate relational constraints, clues, solve, validate, reduce clues, score quality, write metadata, or render PDFs.

### Internal relational constraint derivation

`PuzzleGenerator` owns relational constraint derivation as a private implementation detail. There is no public `ConstraintGenerator` in Version 1.0. After `FixedPositionGenerator` returns mandatory anchors and the target solution, relational derivation sorts the solution by position and creates only non-fixed true positional constraints: direct-left/direct-right or undirected adjacent constraints only for neighboring ordered items, and ordinary left-of/right-of constraints only for longer-range relationships with distance >= 2. For each eligible pair, relation category choices use the injected `random.Random` source so identical seeds are deterministic while different seeds can vary. Visible subset selection validates unique solvability, scores distribution quality, collects all tied best subsets, and chooses among those ties with the same injected random source. Relational derivation must not create additional `FixedPositionConstraint` instances. Derived constraints are de-duplicated and verified against the generated solution.

### `ConstraintDistributionPolicy`

Analyzes the list of generated constraints after fixed anchors and private relational derivation, before clues are rendered. It receives only neutral context such as `required_fixed_count`, counts supported constraint classes, applies deterministic rule-based acceptance, and provides a small tuple score for quality selection and reduction tie-breaking. It does not import or depend on `Difficulty`/`DifficultyPolicy`, classify Easy/Medium/Hard, solve puzzles, generate solutions, validate uniqueness, render PDFs, translate clues, or introduce new constraint types. Diversity is a human-facing quality optimization, not a correctness rule; `DifficultyPolicy` remains authoritative for difficulty and `Validator` remains authoritative for unique solvability.

Normal four-item quality rules allow one- or two-relation sets, but reject three-or-more-relation sets that contain only one relation type, contain more than two of one relation type, or consist entirely of ordinary left/right relations. The deterministic score is lexicographic and explainable: more distinct relation types rank higher, repeated and dominant types rank lower, and remaining tuple fields are neutral stable placeholders rather than direct-relation bonuses.

### `ClueGenerator`

Converts supplied constraint instances into deterministic English `Clue` objects for backward compatibility. It supports far-left, far-right, directly-left-of, left-of, directly-right-of, right-of, and next-to wording. It does not create constraints, solve puzzles, reduce clues, or randomize output.

### `ClueReducer`

Attempts a deterministic remove-and-validate pass over human-readable clues. When multiple removable clues are valid alternatives, it prefers the candidate with the higher `ConstraintDistributionPolicy` score so diversity is preserved where possible. It removes a `Clue` and its corresponding `Constraint` together, never validates hidden constraints, and only accepts removals when `Validator.has_unique_solution()` remains true for the visible constraints that remain and the exact requested fixed-position count is preserved. For normal four-item puzzles it preserves at least two visible clue meanings when a varied valid alternative is available.

### `PuzzleGenerator`

Coordinates the complete pipeline and validates every stage. It accepts optional injected `SolutionGenerator`, `FixedPositionGenerator`, `ClueGenerator`, `Validator`, and `ClueReducer` instances for tests and compatibility. It retries up to `max_attempts` and raises `RuntimeError` with the last failure when generation cannot produce a valid uniquely solvable puzzle.

Pipeline:

```text
Source template/items
        ↓
Difficulty selection
        ↓
FixedPositionGenerator
        ↓
Target Solution + mandatory fixed constraints
        ↓
Relational constraint derivation
        ↓
ConstraintDistributionPolicy
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

During generation, `PuzzleGenerator` assembles multiple valid candidate puzzles when possible. For Version 1 four-player puzzles, it selects the required number of relational clues up front (one for Easy, two for Medium, three for Hard) so all difficulties have exactly three visible clues before reduction. Each candidate is validated for uniqueness before clue reduction, reduced with visible clues and matching constraints removed together, and validated again after reduction. Uniqueness is always validated against the constraints that correspond to visible clues; hidden constraints are forbidden.

After collecting valid candidates, `PuzzleGenerator` scores each candidate with a deterministic internal quality heuristic and returns the highest-scoring puzzle. Multiple candidates are generated because the first uniquely solvable clue set can be mathematically valid but repetitive for a human player; comparing several valid reduced alternatives lets the generator prefer a more varied visible clue set without changing solver, reducer, or public API behavior.

The quality score is based on constraint type and `ClueType`, not rendered English text, so scoring stays independent from localisation, clue wording, and PDF presentation. Distribution scoring is tuple-based rather than weighted: it compares distinct relation-type count, repeated relation penalties, dominance, adjacency presence, and direct-neighbour presence. The quality heuristic is separate from difficulty classification and only compares candidates that already pass distribution acceptance, unique-solution validation, and the requested difficulty check.

The number of valid candidates considered is controlled by the internal `QUALITY_CANDIDATE_COUNT` constant. Seeded `random.Random` inputs remain deterministic because candidate generation consumes randomness in a stable sequence, every valid candidate is scored with a pure deterministic function, and ties are resolved by the stable order of the generated candidate list.

## 7. Localization and PDF packages

`Language` defines supported presentation languages: `Language.ENGLISH` (`en`) and `Language.GERMAN` (`de`). `TranslationCatalog` centralizes PDF headings, labels, CLI-facing output labels, and metadata-title translations. `ClueTextRenderer` renders clue wording from each clue's linked constraint in the selected language. This keeps German wording out of constraints, solver, validator, and generator logic. English remains the default and uses stored `Clue.text` for backward compatibility.

PDF difficulty labels are localized presentation text: English maps numeric metadata `1`, `2`, and `>=3` to `Easy`, `Medium`, and `Hard`; German maps them to `Leicht`, `Mittel`, and `Schwierig`. Missing difficulty omits the line, while invalid values fail clearly. German PDF output uses Swiss-compatible spelling without `ß`, for example `Tennistraining`, `Thema`, `Schwierigkeit`, `Hinweise`, `Trage die Namen ein`, `Verfügbare Namen`, and `Lösung`.

## 8. PDF package

`TextRenderer` renders clues, solution rows, and item names as strings. It validates that rendered text is human-readable.

`GirlFigureRenderer` draws anonymous Tennis-themed girl placeholders using ReportLab primitives only. It has no puzzle logic and does not know player names or solutions.

`PlayerLineupRenderer` is a reusable ReportLab flowable for the horizontal lineup. Its layout maps slot index `0..3` to visible positions `1..4` from left to right, draws one writable box per slot, and optionally accepts already-rendered labels for the solution PDF.

`PdfGenerator` writes A4 portrait ReportLab PDFs:

- `create_puzzle_pdf(puzzle, filename)` writes the unsolved puzzle PDF with localized clues, four anonymous figures, empty name boxes, position numbers, and available names.
- `create_solution_pdf(puzzle, filename)` writes the solved PDF with the same lineup and labels taken from `puzzle.solution.assignment`.
- `create(puzzle, filename)` is a backward-compatible wrapper for `create_puzzle_pdf()`.

PDF generation is presentation-only. It must not derive constraints, solve puzzles, reveal solution names in unsolved boxes, or alter puzzle data.

## 9. Theme and entry-point flow

`themes.tennis.create_template()` returns the built-in Tennis `PuzzleTemplate`.

`create_puzzle.create_puzzle()` generates that template and writes both default PDFs. It accepts `language="en"`, `language="de"`, or a `Language` value; English is the default. Difficulty may be `easy`, `medium`, `hard`, a `Difficulty` value, or `None` to choose randomly:

```text
output/puzzle_3.pdf
output/puzzle_3_solution.pdf
```

## 10. Data flow

```text
Theme/PuzzleTemplate or Item iterable
        ↓
Difficulty selection
        ↓
FixedPositionGenerator
        ↓
Target Solution + mandatory fixed constraints
        ↓
Relational constraint derivation
        ↓
ConstraintDistributionPolicy
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

### `DifficultyPolicy`

`DifficultyPolicy` runs after `ClueReducer` and final uniqueness validation. It accepts the final `Puzzle` (or final visible constraints), counts only visible `FixedPositionConstraint` instances, and stores `1`, `2`, or `3` in copied puzzle metadata. Easy means exactly two fixed-position clues, Medium means exactly one, and Hard means zero. Other relation constraints do not count. Version 1 four-player puzzles always expose exactly three visible clues: Easy has one relational clue, Medium has two, and Hard has three.

Updated generation order:

```text
Difficulty selection -> FixedPositionGenerator -> target Solution + mandatory fixed constraints
-> private relational constraint derivation -> ConstraintDistributionPolicy -> ClueGenerator -> Validator
-> ClueReducer (clues and matching constraints together, exact fixed count preserved) -> Validator
-> DifficultyPolicy match/classify -> quality selection among matching candidates -> PdfGenerator presentation
```


## 11. Localization and wording variation

Localized clue prose is a presentation concern. The flow is:

```text
Constraint
  ↓
ClueTextRenderer
  ↓
TemplateCatalog
  ↓
localized rendered sentence
```

`TemplateCatalog` stores multiple English and German templates for each existing visible constraint type using named placeholders. `ClueTextRenderer` extracts semantic roles from the constraint, selects one equivalent template using its injected `random.Random` instance, and formats the sentence. This gives deterministic wording for identical seeds and natural variation across different seeds while keeping mathematical constraints, solving, validation, generation, difficulty, clue reduction, and PDF layout unchanged.


## 12. Build-quality regression gates

GitHub Actions runs the normal pytest suite on push and pull request, and that suite includes `tests/generator/test_relation_distribution_regression.py`. The test is an architectural boundary check for generator output quality: `PuzzleGenerator` still generates visible constraints, `ConstraintDistributionPolicy` scores variety, `DifficultyPolicy` owns the fixed-position difficulty rule, and `Solver`/`Validator` remain correctness authorities. The regression gate only observes generated Tennis puzzles over fixed seed ranges (`10000-10199`, `20000-20199`, `30000-30199`) and asserts deterministic relation-type distribution thresholds for the five supported visible relation classes.
