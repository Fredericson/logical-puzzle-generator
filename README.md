# Logical Puzzle Generator

Logical Puzzle Generator creates small, printable Einstein-style ordering puzzles and verifies them mathematically before returning them. Version 1.0 focuses on a stable 4-item puzzle pipeline: generate a solution, derive constraints, apply a deterministic constraint distribution policy for clue variety, convert them to clues, validate uniqueness, reduce redundant clues, and render child-friendly A4 puzzle and solution PDFs.

## Version 1.0 capabilities

- Generate a complete one-to-one assignment of puzzle items to positions.
- Derive internal mathematical constraints from the generated solution.
- Convert supported constraints into human-readable clues and render deterministic localized wording variations for PDFs.
- Validate that a puzzle has exactly one solution using the brute-force solver.
- Reduce unnecessary clues while preserving unique solvability and at least one clue.
- Generate printable A4 puzzle and solution PDFs with ReportLab in English (`en`, default) or German (`de`).
- Render a polished Version 1 worksheet layout with a balanced title/metadata area, generous whitespace, readable clue wrapping, and identical puzzle/solution alignment.
- Render the Tennis puzzle as a horizontal child-friendly lineup of four anonymous vector girls, larger writable handwriting boxes, and left-to-right position numbers.
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
from logical_puzzle_generator.model.item import Item

children = [Item("Aurelia"), Item("Emma"), Item("Lara"), Item("Mia")]
puzzle = PuzzleGenerator().generate(children)
print([clue.text for clue in puzzle.clues])
```

The puzzle PDF uses A4 portrait output. Its child-friendly layout shows four anonymous vector girls from left to right, one larger empty writable name box per position, position numbers 1-4, localized clues with hanging indentation, and a separate available-names list. The title area can show the puzzle number supplied by the creation entry point, the localized difficulty label, and the theme without exposing numeric difficulty metadata. The solution PDF reuses the same layout grid and only fills the boxes from `puzzle.solution.assignment` without solving again.

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
  generator/      SolutionGenerator, FixedPositionGenerator, ConstraintDistributionPolicy, ClueGenerator, ClueReducer, PuzzleGenerator, PuzzleBookGenerator, PuzzleTemplate
  pdf/            TextRenderer, vector lineup renderers, and PdfGenerator presentation layer
  localization.py Language enum and translation catalog
  clue_text_renderer.py Localized clue wording for presentation
  themes/         Built-in data-driven theme definitions and registry
  create_puzzle.py Convenience script for generating themed PDFs

tests/            Pytest coverage for model, engine, generator, and PDF behavior
docs/             Version 1.0 project documentation and AI workflow guidance
examples/         Placeholder for generated example artifacts and future examples
```

## Deterministic relation-distribution regression gate

The normal pytest suite includes `tests/generator/test_relation_distribution_regression.py`, a deterministic statistical quality gate for visible Tennis relation clues. It generates 600 puzzles from explicit integer seed ranges: Easy `10000-10199`, Medium `20000-20199`, and Hard `30000-30199` (200 puzzles per difficulty). The gate counts only `DirectLeftOfConstraint`, `LeftOfConstraint`, `DirectRightOfConstraint`, `RightOfConstraint`, and `AdjacentConstraint`; it intentionally excludes `FixedPositionConstraint`.

The regression suite owns the exact numeric quality thresholds. Conceptually, every supported relation type has deterministic lower and upper representation limits, and ordinary non-direct `LeftOfConstraint` plus `RightOfConstraint` must maintain a minimum combined share. Exact measured counts are intentionally not documented as requirements; when a regression occurs, the test diagnostics print the total, per-type counts, percentages, difficulty sample sizes, and seed ranges. This is a generator quality regression test, not solver correctness logic; every sampled position-only compatibility puzzle is still checked for the requested difficulty mix, unique solvability, solution equality, and the retained relation-distribution gates.

Run it locally with:

```bash
pytest tests/generator/test_relation_distribution_regression.py
```

It is part of the standard CI build, so `pytest` runs it automatically on push and pull request.

## Documentation

Start with `docs/README.md`. The main documents are:

- `docs/01_AI_DEVELOPMENT_SPEC.md`
- `docs/02_ARCHITECTURE.md`
- `docs/03_CONTRIBUTING_AI.md`
- `docs/04_ROADMAP.md`
- `docs/05_DECISIONS.md`
- `docs/06_PROMPTS.md`

## Language support

English is the default for backward compatibility. German can be selected with `--language de`, `create_puzzle(..., language="de")`, or `PdfGenerator(language="de")`. Public callers may also use `Language.GERMAN`. Unsupported language values are rejected instead of silently falling back. Localization is presentation-only: solver, validator, constraints, and generation semantics remain language-independent. Difficulty is selected at generation time (omit it or pass `None` to choose randomly). For Position pages and standalone puzzles, Difficulty is determined by the final visible child `FixedPositionConstraint` count: Easy has exactly two, Medium has exactly one, and Hard has zero. Position-only compatibility puzzles may retain the three-clue shape. Commit 12.6 PuzzleBook Theme pages use fixed children from Page 1, so their Difficulty is determined by final visible distinct direct Theme-value assignments: Easy has exactly two, Medium has exactly one, and Hard has zero. Direct Theme assignments may map a Theme value to a child or to a position; equivalent child-based and position-based clues normalize to one revealed assignment, and relative clue counts vary according to unique solvability. The numeric metadata remains `1`/`2`/`3`; PDFs only render localized labels (`Easy`/`Medium`/`Hard` or `Leicht`/`Mittel`/`Schwierig`).

### Selectable difficulty

Generated puzzles choose a random difficulty when `--difficulty` is omitted or `create_puzzle(..., difficulty=None)` is used. A specific level may be requested with `--difficulty easy`, `--difficulty medium`, or `--difficulty hard`, or programmatically with `create_puzzle(..., difficulty="easy")` / `Difficulty.EASY`. Difficulty is based on direct assignments for the active page task. For Position pages and standalone puzzles, Easy `== 2`, Medium `== 1`, and Hard `== 0` visible child-position assignments. Direct-left, direct-right, adjacent, left-of, and right-of clues do not count as fixed-position clues. For fixed-child PuzzleBook Theme pages, Easy `== 2`, Medium `== 1`, and Hard `== 0` distinct directly revealed Theme-value assignments. A direct Theme assignment can be a child-to-value clue such as `Emma has the blue bag` or a value-to-position clue such as `Position 3 has the blue bag`; if Page 1 says Emma is in Position 3, those two clues reveal the same Theme cell and count once, not twice. Relative clues do not count, and their count may vary to preserve unique solvability. Generation uses the injected random source to choose direct anchors, eligible adjacent/non-adjacent relation semantics, and tied best visible relation subsets; it builds a solution consistent with those choices and retries until the final visible direct-assignment count matches the requested level; PDF localization only maps stored `1/2/3` metadata to labels.


### Clue variety policy

`ConstraintDistributionPolicy` analyzes generated constraints before clue text is created. It receives only neutral distribution context, such as the required fixed-position count, and does not understand Easy, Medium, or Hard. Its rule-based acceptance rejects obviously repetitive four-item relation mixes, while its small deterministic comparison score ranks relation variety neutrally by distinct relation types, fewer repeats, and lower dominance; adjacency and direct-neighbour clues are not preferred defaults. This is a quality optimization only: `DifficultyPolicy` owns difficulty, solver and validator uniqueness checks remain the correctness authority, and no new clue or constraint types are introduced. The reducer uses the same score only as a tie-breaker after difficulty preservation and uniqueness have already been checked.


## Localized clue wording variations

Visible constraints remain mathematical, language-independent objects. At render time, `ClueTextRenderer` maps each supported constraint to named placeholder values and asks `TemplateCatalog` for English or German wording templates. One equivalent template is selected per clue with the renderer's `random.Random` source, so seeded rendering is deterministic while different seeds can vary the prose naturally. German templates use Swiss spelling and must not contain `ß`.


## Version 1 presentation polish

Commit 12.1 is presentation-only. It polishes the child-facing PDF worksheet with calmer spacing, a clearer typography hierarchy, larger name boxes, deterministic lineup geometry, and aligned wrapped clue numbering. It does not change generated constraints, clue wording templates, clue order, clue counts, difficulty classification, localization semantics, solver behavior, validator behavior, puzzle numbering semantics, or metadata.

## Commit 12.2 themed puzzles

Puzzles now support five data-driven child-friendly themes: `tennis_training`, `dance_studio`, `beach_day`, `athletics_training`, and `zoo_visit`.  Each generated Version 1 puzzle keeps four child protagonists and four ordered positions, and adds exactly one selected category instance with four distinct values.  Select a theme with `--theme beach_day` or with the public API `create_puzzle(..., theme="beach_day")`; omitting the theme remains backward-compatible and uses `tennis_training`.  `--theme random` selects one supported theme through the generator random source.

The solver is category-aware: children and the selected thematic value category instance are permuted independently, giving a 4! × 4! space rather than an unrestricted 8! space.  Standalone themed puzzle difficulty still means only the visible fixed child-position anchors: easy has 2, medium has 1, hard has 0. The worksheet renders bordered choice boxes for available names and possible thematic values.

### Theme presentation and clue counts

Theme values have internal IDs and localized display labels. Internal IDs are never intended for child-facing output; clue text, solution labels, and PDF choice boxes resolve values through the theme presentation resolver. Direct assignment clue grammar is theme-specific, for example tennis uses “practises/trainiert”, dance uses “dances/tanzt”, beach uses activity fragments, athletics uses “practises/übt”, and zoo uses “visits/besucht”.

Themed puzzles do not have a universal three-clue count. They are reduced while preserving unique solvability across child positions and the selected thematic category instance, exact child-position anchor difficulty, one visible clue per mathematical constraint, and no hidden constraints. Position-only compatibility paths may still retain the original three-clue behavior.

### Commit 12.3 PuzzleBooks

`PuzzleBookGenerator` builds a multi-page book for exactly one selected registry theme. It selects the four children once from the shared child source, reuses those same `Item` objects on every generated page, creates a position-only first puzzle with no theme metadata, then creates the requested number of one-category theme puzzles. Theme categories are selected only from the resolved `ThemeDefinition.categories`: selection avoids repetition while enough registered categories are available and reuses registered categories only after that pool is exhausted. Reused categories keep their category ID but receive distinct `theme_category_instance_id` metadata values.

Every `PuzzleBook` exposes a derived, presentation-neutral summary table. In the current Commit 12.6 model its columns are Position 1-4, the first row is `Name`, and subsequent rows come one-for-one from Theme pages using `theme_category_instance_id` as their internal identity. The Position puzzle is never a Theme summary row. The PuzzleBook puzzle PDF contains the Position page, all Theme pages, and a final empty summary table that does not reveal solved child names. The PuzzleBook solution PDF contains only the completed summary table, not solved copies of every individual puzzle. Commit 12.4 extends this PuzzleBook flow with the generated numeric `tournament_wins` category while preserving position-based summary derivation.

### Commit 12.5 racket-count numeric tennis puzzles

Commit 12.5 adds `racket_count` as a second production numeric category. It is registered only for the `tennis_training` theme with the labels `Rackets in Bag` and `Schläger in der Tasche`. The category describes how many tennis rackets each child carries in her bag, using small child-friendly values in the range 1-8. The generated page still selects exactly four distinct positive integers and includes a factor-2 relationship, but the set is generated per category instance rather than hardcoded.

Example English clues include `Emma has 4 rackets in her bag.`, `Mia has 1 fewer racket in her bag than Emma.`, and `Aurelia has twice as many rackets in her bag as Mia.` German clues use Swiss spelling, for example `Emma hat 4 Schläger in ihrer Tasche.`, `Mia hat 1 Schläger weniger in ihrer Tasche als Emma.`, and `Aurelia hat doppelt so viele Schläger in ihrer Tasche wie Mia.`

The implementation reuses the Commit 12.4 numeric architecture: generated value IDs remain category-neutral and instance-scoped (`<theme_category_instance_id>_value_<integer>`), arithmetic clues use the existing exact, difference, and factor-2 constraints, and solving remains the category-aware `4! × 4!` child/value permutation model. Standalone numeric-puzzle Difficulty is unchanged: Easy, Medium, and Hard still mean exactly two, one, and zero visible child-position anchors. Inside PuzzleBooks, fixed-child numeric Theme pages use the same distinct direct-assignment rule as text Theme pages: Easy, Medium, and Hard keep exactly two, one, and zero unique direct numeric Theme assignments respectively, and every numeric page also retains at least one relative arithmetic clue. Standalone numeric pages still use the standalone `2/1/0` child-position-anchor contract.

The existing single-puzzle CLI can generate a German racket-count puzzle without a new command or flag:

```bash
python -m logical_puzzle_generator.create_puzzle --theme tennis_training --category racket_count --difficulty easy --language de
```


### Commit 12.4 numeric tournament wins and PuzzleBook CLI

Commit 12.4 adds `tournament_wins` as the first numeric theme category. It is registered only on the `tennis_training` theme and still follows the one-category-per-theme-page model: each page has four children, four positions, and exactly four selected tournament-win value IDs. The child/value pairing is still established by shared solved position, so numeric pages preserve the existing category-aware `4! × 4!` assignment boundary instead of introducing a combined `8!` model.

Tournament-win clues are mathematical domain constraints rendered by the presentation layer. Examples include:

* `Emma won 17 tournaments.`
* `Aurelia won 4 fewer tournaments than Emma.`
* `Emma won 4 more tournaments than Aurelia.`
* `Mia won twice as many tournaments as Sofia.`

German rendering uses Swiss spelling, for example `Mia gewann doppelt so viele Turniere wie Sofia.` Numeric values are stored as stable value IDs plus integer values and are formatted only for clues, choice boxes, solution rows, and PuzzleBook summary tables. Generated numeric value IDs use the category-neutral format `<theme_category_instance_id>_value_<integer>`, for example `tournament_wins_2_value_14`. The category-level parser validates generated ID syntax, the expected category-instance prefix, the numeric suffix, and the configured numeric range; a syntactically valid, correctly scoped, in-range ID can be reconstructed at that level. The reconstructed `ThemeCategoryInstance` then enforces selected membership through `value_by_id()`, so syntactically valid but unselected values cannot be rendered as page values. PDF and clue presentation reconstruct category instances only from `theme_category_instance_id` and `selected_theme_value_ids`, then perform later lookups through that instance. Internal IDs are never child-facing. Final tournament-win pages remain uniquely solvable, include at least one relative arithmetic clue, never consist of four exact numeric assignments, and still use one active theme category per page. Standalone numeric puzzles preserve the standalone Difficulty meaning: Easy has 2 visible child-position anchors, Medium has 1, and Hard has 0. Fixed-child PuzzleBook numeric Theme pages instead use the Commit 12.6 page task: Easy has 2 distinct direct numeric Theme assignments, Medium has 1, and Hard has 0. Difficulty counts directly revealed answers rather than raw clue objects; for example, if Page 1 fixes Emma to Position 2, “Emma has the blue bag” and “The blue bag is in Position 2” reveal the same Theme cell and count as one direct assignment. The same numeric mechanism can be reused by future numeric categories through a category ID, numeric range, localized wording, and the existing arithmetic constraints without solver changes.

The official PuzzleBook entry point is:

```bash
python -m logical_puzzle_generator.create_puzzle_book --theme tennis_training --pages 8 --difficulty easy --language de
```

By default it writes:

```text
output/puzzle_book.pdf
output/puzzle_book_solution.pdf
```

`--pages` counts Theme pages only; the generated puzzle PDF also includes one Position page and one final empty summary page. Passing `--pages 0` is supported intentionally and creates only the Position page plus the empty summary page in the puzzle PDF. The solution PDF contains only the completed summary table. Use `--seed` for deterministic theme/category/value/solution generation:

```bash
python -m logical_puzzle_generator.create_puzzle_book --theme tennis_training --pages 8 --difficulty easy --language de --seed 42
```

### Commit 12.6 stable PuzzleBook progression

PuzzleBooks now use Page 1 as the permanent child-order authority. The Position puzzle establishes which child belongs to Position 1, Position 2, Position 3, and Position 4, and that same order applies to every later Theme page. Available names are shown only on the Position page; Theme pages reuse the Page-1 child order and ask only for the selected Theme category values by position.

PuzzleBook worksheet pages render a consistent child-facing header with Theme, Question, and Difficulty. The Position page question is the localized order-of-children prompt, while Theme pages use the localized category label such as tennis bag colour, tournament wins, or rackets in bag rather than internal category IDs.

PuzzleBook summaries now use Position 1-4 columns plus an explicit Name row. The unsolved summary leaves the Name row and Theme-answer cells empty so it does not reveal the Position solution. The solved summary uses the same table shape and fills the Name row from the Position puzzle solution before filling one row per Theme page.

The solving models are intentionally different by context: standalone themed puzzles remain complete `4! × 4!` puzzles that solve both child positions and Theme values independently, the PuzzleBook Position page solves the `4!` child order, and each PuzzleBook Theme page constructs exactly one fixed child assignment times `4!` Theme-value assignments.
