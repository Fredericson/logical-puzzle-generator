# Architecture Decision Records

This document records accepted architectural decisions for Version 1.0.

## ADR-001: Use Python

Status: Accepted

Decision: implement the project in Python.

Reason: Python is readable, easy to test, and approachable for contributors.

## ADR-002: Keep a package-oriented architecture

Status: Accepted

Decision: separate responsibilities into `model`, `constraints`, `engine`, `generator`, `pdf`, and `themes` packages.

Reason: clear package boundaries make the repository easier to maintain and reduce accidental coupling.

## ADR-003: Use brute-force solving for Version 1.0

Status: Accepted

Decision: keep the solver as a straightforward brute-force permutation checker with optional early exit.

Reason: Version 1.0 targets four active items, where brute force is simple, deterministic, and fast enough.

## ADR-004: Represent domain concepts explicitly

Status: Accepted

Decision: use explicit objects such as `Item`, `Position`, `Category`, `Puzzle`, `Clue`, and `Solution` rather than passing primitive strings and dictionaries everywhere.

Reason: explicit domain models improve readability and make public APIs easier to understand.

## ADR-005: Keep constraints independent

Status: Accepted

Decision: each constraint implements `matches(assignment)` and exposes `description` without depending on other constraints.

Reason: independent constraints keep the solver generic and make clue conversion straightforward.

## ADR-006: Separate solver, generator, and PDF rendering

Status: Accepted

Decision: the solver validates puzzles, the generator creates puzzles, and the PDF package renders existing puzzle data.

Reason: keeping these responsibilities separate prevents presentation or generation details from leaking into mathematical verification.

## ADR-007: Preserve stable architecture boundaries

Status: Accepted

Decision: future work should extend the current boundaries instead of replacing the solver, validator, assignment model, constraint hierarchy, or generator orchestration without an explicit ADR.

Reason: predictable boundaries help human and AI contributors make safe incremental changes.

## ADR-008: Prefer complete implementations over placeholders

Status: Accepted

Decision: do not merge placeholder code, mock implementations, or TODO-driven behavior.

Reason: incomplete code obscures repository status and slows future development.

## ADR-009: Make `PuzzleGenerator` the Version 1.0 orchestration boundary

Status: Accepted

Decision: `PuzzleGenerator` coordinates solution generation, private constraint derivation, clue generation, uniqueness validation, clue reduction, final validation, retry handling, and clear generation failure messages.

Reason: this keeps robustness checks in one orchestration boundary while reusing `SolutionGenerator`, `ClueGenerator`, `ClueReducer`, and `Validator`.

## ADR-010: Keep constraint derivation internal for Version 1.0

Status: Accepted

Decision: do not expose a public `ConstraintGenerator` in Version 1.0. Constraint derivation remains a private `PuzzleGenerator` implementation detail.

Reason: the current derivation is intentionally narrow and tied to the Version 1.0 ordering-puzzle pipeline. A public abstraction would imply extension points that are not yet stable.

## ADR-011: Treat PDF generation as presentation-only

Status: Accepted

Decision: `TextRenderer` and `PdfGenerator` render existing puzzles and must not solve, generate, or mutate puzzle logic.

Reason: this preserves a clean dependency direction and keeps PDF behavior testable independently from generation.


## ADR-012: Visible clues and constraints remain one-to-one

Status: Accepted

Decision:

- Every visible clue owns exactly one `Constraint`.
- `ClueReducer` removes a `Clue` and its corresponding `Constraint` together.
- `Validator` validates only visible constraints.
- Hidden constraints are forbidden.
- Direct-left and direct-right relationships are explicit constraint types.
- Fixed-position endpoint clues render as "far left" and "far right".

Rationale: puzzles must not appear ambiguous to the player while remaining unique internally. The visible clue set and the mathematical constraint set therefore stay aligned throughout generation, reduction, validation, and PDF rendering.


## ADR-013: Select the highest-quality valid generated candidate

Status: Accepted

Decision: `PuzzleGenerator` generates multiple valid candidate puzzles when possible, validates unique solvability before and after clue reduction, scores the reduced visible clue sets with a deterministic quality heuristic, and returns the highest-scoring candidate.

The internal quality score rewards varied clue meanings, endpoint clues, adjacent clues, direct-left/direct-right clues, and balanced clue distributions. It penalizes duplicate clue meanings and candidates dominated by one clue meaning. Scoring is based on constraint type and `ClueType`, not rendered clue text, so it remains independent from localisation and PDF wording. Candidate count is controlled by the internal `QUALITY_CANDIDATE_COUNT` constant rather than by a new public API.

Rationale: Version 1.0 already guarantees mathematical correctness and unique solvability. Human-facing quality improves when the generator can compare several valid alternatives instead of returning the first valid puzzle. Keeping the selection stage inside `PuzzleGenerator` preserves the existing Solver, Validator, ClueReducer, PDF, and public API boundaries while maintaining deterministic output for seeded random sources.


## ADR-014: Keep localization in the presentation layer

Status: Accepted

Decision: support English and German through a small internal `Language` abstraction, `TranslationCatalog`, and `ClueTextRenderer`. Constraints, solver, validator, and generator remain language-independent. English clue text stored on `Clue` remains backward compatible; localized PDF clue wording is rendered from the clue's one-to-one constraint in the presentation layer.

Rationale: localization changes how a puzzle is presented, not what mathematical constraints mean or how puzzles are generated and validated. Centralizing translated labels and clue wording avoids scattered language checks while preserving existing architecture boundaries.


## ADR-015: Render the Tennis PDF as a reusable vector lineup

Status: Accepted

Decision: replace the technical vertical solving table in generated PDFs with an A4 portrait, child-friendly horizontal lineup for the four-player Tennis puzzle. The PDF package owns `GirlFigureRenderer` for anonymous ReportLab vector figures and `PlayerLineupRenderer` for left-to-right position slots, writable boxes, and optional solved labels.

Rationale: the puzzle is intended to be understood visually by children. Keeping illustrations and lineup geometry in focused PDF components preserves the presentation-only boundary: generator, solver, validator, constraints, language semantics, difficulty, and numbering remain unchanged. The solution PDF can safely share the same layout by receiving labels derived from `puzzle.solution.assignment` rather than solving again. Difficulty remains numeric metadata classified by the generator from final visible fixed-position clues; localized child-facing difficulty labels are provided by the presentation/localization layer for both puzzle and solution PDFs.

## ADR-016: Superseded heuristic difficulty estimate

Decision: superseded by ADR-017. The old score-based difficulty heuristic is no longer the authoritative difficulty definition.

Rationale: child-facing difficulty should describe the puzzle the player actually receives. Removed clues, hidden/original constraints, rendered wording, PDF language, and the target solution must not shortcut the estimate.

Current rule: see ADR-017. Difficulty is based on final visible direct assignments for the active page task.

Consequences: future generated clue/constraint types must define their difficulty impact before they are made visible. PDF localization remains presentation-only: `TranslationCatalog` maps stored numeric values to English/German labels and does not estimate difficulty.

## ADR-017: Select difficulty by visible direct-assignment count

Decision: ADR-016 is superseded for Version 1 difficulty classification. `DifficultyPolicy` is the authoritative classifier and inspects only final constraints that correspond one-to-one with visible clues. Easy means exactly two distinct visible direct assignments, Medium means exactly one, and Hard means zero. Position pages and standalone puzzles count child-position `FixedPositionConstraint` anchors. Fixed-child PuzzleBook Theme pages count canonical direct Theme-value identities, including child-to-value `SamePositionConstraint` clues, Theme-value-to-position `FixedPositionConstraint` clues, and exact numeric child-to-value clues. Direct-left, direct-right, adjacent, left-of, right-of, numeric-difference, and numeric-multiple constraints are relative clues and never count toward Difficulty. Total clue count and raw constraint-instance count are not Difficulty measures; equivalent direct clues normalize through inherited child positions and selected Theme values to the same revealed answer.

Rationale: the previous heuristic often labelled puzzles Medium even when they were too difficult for the intended child, and fixed-child PuzzleBook pages need Difficulty to describe the page task rather than hidden inherited child positions. A direct-assignment-count rule is predictable, testable, independent of language/PDF text, and based on the answers directly revealed on the page the child actually sees.

Consequences: `PuzzleGenerator` accepts an optional requested difficulty (omitted/`None` chooses randomly with the injected random source), delegates mandatory child-position assignment and target solution construction to `FixedPositionGenerator` for Position/standalone pages, and for fixed-child Theme pages selects exact distinct direct identities before choosing one clue variant for each identity and adding a variable relative subset for unique solvability. Clue reduction and final validation preserve the exact direct-assignment count, numeric Theme pages also retain at least one relative arithmetic clue, and generation retries until a matching candidate is found or raises a clear `RuntimeError` after `max_attempts`. Numeric metadata remains `1` Easy, `2` Medium, and `3` Hard. PDF and translation components render stored metadata only and do not recalculate difficulty.


## ADR-018: Use a deterministic constraint distribution policy for clue variety

Decision: `ConstraintDistributionPolicy` analyzes generated fixed and relational constraints before clue generation, rejects clearly poor type distributions with neutral context such as `required_fixed_count`, and scores acceptable distributions for quality selection and reducer tie-breaking. It uses only the existing Version 1 constraint types, deterministic rule checks, and a small tuple score based on relation-type variety, repeats, and dominance without making direct-neighbour clues preferred defaults.

Rationale: uniqueness and difficulty rules make puzzles correct, but balanced clue types make them more enjoyable. Keeping distribution scoring separate preserves Solver, Validator, FixedPositionGenerator, ClueGenerator, ClueReducer, DifficultyPolicy, and PdfGenerator responsibilities. The policy deliberately does not import or depend on `Difficulty` or `DifficultyPolicy`; those remain the only difficulty-classification boundary.

Consequences: clue diversity can improve without changing mathematical correctness. Relational generation keeps adjacent semantics separate from non-adjacent ordinary left/right semantics, and visible selection chooses among equally scored best subsets with the injected seeded random source. Poor distributions are retried before expensive later stages, while final visible puzzles are still validated for unique solvability and exact requested difficulty. ADR-017 remains unchanged: difficulty is still classified only by final visible `FixedPositionConstraint` count.

## ADR-011: Keep clue wording variation in the presentation layer

Status: Accepted

Decision: localized natural-language clue variations belong exclusively to the presentation layer. `ClueTextRenderer` renders a semantic `Constraint` by asking `TemplateCatalog` for localized templates and selecting one with the injected `random.Random` source.

Reason: constraints define mathematical truth through `matches(assignment)`, while wording is user experience. Keeping templates out of constraints, solvers, validators, generators, difficulty policy, and PDF layout preserves identical puzzle semantics and allows wording/localization to evolve safely.

Consequences:

- constraint objects remain language-independent;
- template selection is deterministic when callers inject a seeded random source;
- English and German clue variants can change without changing generated clue counts or solver behavior;
- localized templates must use named placeholders and Swiss German spelling without `ß`.


## ADR-019: Gate relation-distribution quality in CI

Status: Accepted

Decision: treat visible relation distribution as a deterministic build-quality gate. The standard pytest suite runs a statistical regression test over the Tennis four-player template using Easy seeds `10000-10199`, Medium seeds `20000-20199`, and Hard seeds `30000-30199`. It counts only `DirectLeftOfConstraint`, `LeftOfConstraint`, `DirectRightOfConstraint`, `RightOfConstraint`, and `AdjacentConstraint`. The regression suite owns the exact numeric thresholds: each supported relation type has deterministic lower and upper quality limits, and ordinary non-direct left/right clues have a minimum combined representation.

Rationale: solver uniqueness and exact fixed-position difficulty rules prove correctness, but they do not protect against silent quality regressions where a supported clue meaning disappears. Fixed seed ranges make the gate reproducible and non-flaky while catching severe starvation and dominance.

Consequences: generator changes must preserve relation variety or update the regression-suite thresholds with deterministic evidence. Exact measured counts are emitted by failing test diagnostics rather than documented as architectural requirements. The test remains observational; no solver, validator, difficulty, PDF, localization, or generator-balancing responsibilities move into CI.


## ADR-020: Polish Version 1 PDFs without changing puzzle semantics

Status: Accepted

Decision: child-facing PDF polish is presentation-only. `PdfGenerator` and `PlayerLineupRenderer` may adjust margins, spacing, typography hierarchy, clue indentation, deterministic vector geometry, and solution-label filling, but they must not change generated constraints, visible clue count, clue order, clue wording templates, relation distribution, difficulty classification, localization semantics, solver behavior, validator behavior, puzzle numbering semantics, or metadata.

Rationale: Version 1 is feature-complete, so the worksheet should feel professionally printed and pleasant to solve with a pencil while preserving the already validated puzzle semantics. Keeping puzzle and solution PDFs layout-identical except for filled solution names makes visual regression testing straightforward and preserves the existing architecture boundary that rendering consumes puzzle data rather than producing or interpreting it.

## ADR-021: Exactly one selected category instance in Commit 12.2

Commit 12.2 adds selectable data-driven themes while deliberately keeping Version 1 puzzles small: four children, four positions, and one selected category instance with four values from a multi-category theme.  This gives children one meaningful additional dimension to solve without introducing multiple categories, animal protagonists, 5×5 puzzles, or batch/PDF complexity.

## ADR-022: Category-aware solver assignments

The assignment model now treats children and thematic values as separate categories that independently occupy the same four positions.  This preserves one-to-one semantics per category and keeps the search space at 4! × 4!, avoiding an unrestricted 8! flattening.  Difficulty calibration remains isolated to direct assignments for the active page task; inherited fixed child positions do not count on fixed-child Theme pages.

## ADR-023: Deferred PuzzleBook structure

Decision: documentation now records the future PuzzleBook shape without adding production PuzzleBook classes or multi-page generation. A future book will use exactly one theme, stable names throughout the PDF, a universal position page first, multiple later pages that each select one theme category instance, optional repeated category instances with distinct IDs, and a final summary page. Commit 12.2 remains a one-page generator and does not implement book orchestration, repetition scheduling, or summary rendering.

The future PuzzleBook puzzle PDF will contain the Position page, theme-category puzzle pages, and the final empty summary table. The PuzzleBook solution PDF does not need separately solved copies of every previous puzzle page; the filled summary table is the only required solution presentation for the book. Summary columns are the stable child names ordered by the first Position puzzle. Summary rows come only from theme-category pages; the Position page is not a row. No additional solver run is performed for the summary table because cells are derived from already generated page solutions. The current Commit 12.2 single-page API continues to emit its normal single-page puzzle and solution PDFs.

Future numeric categories such as `tournament_wins` are deferred to a dedicated numeric-category commit. They may use positive distinct integer values and child-friendly addition/subtraction comparison clues, but Commit 12.2 adds no numeric constraints, arithmetic generators, placeholders, multiplication, or division.
