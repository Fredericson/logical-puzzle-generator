# DECISIONS.md

# Architecture Decision Record (ADR)

This document records the most important architectural decisions.

------------------------------------------------------------------------

## ADR-001

### Decision

Use Python as implementation language.

### Reason

-   Excellent readability
-   Strong ecosystem
-   Easy contribution
-   Great testing support

Status: Accepted

------------------------------------------------------------------------

## ADR-002

### Decision

Keep the project package-oriented.

Packages

-   model
-   constraints
-   engine
-   generator
-   pdf
-   themes

Reason

Clear separation of responsibilities.

Status: Accepted

------------------------------------------------------------------------

## ADR-003

### Decision

Use brute-force solving.

Reason

For 4×4 puzzles brute force is fast enough and dramatically simpler than
complex constraint propagation.

Status: Accepted

------------------------------------------------------------------------

## ADR-004

### Decision

Represent domain concepts explicitly.

Use

-   Item
-   Position
-   Category
-   Puzzle

instead of primitive strings whenever appropriate.

Reason

Improves readability and maintainability.

Status: Accepted

------------------------------------------------------------------------

## ADR-005

### Decision

Keep Constraint classes independent.

Reason

Each constraint answers exactly one question:

matches(assignment)

This keeps the solver generic.

Status: Accepted

------------------------------------------------------------------------

## ADR-006

### Decision

Separate Solver from Generator.

Reason

The solver validates puzzles.

The generator creates puzzles.

Neither component should depend on the other internally.

Status: Accepted

------------------------------------------------------------------------

## ADR-007

### Decision

Preserve the current architecture.

Reason

Future contributors (human or AI) should extend the project instead of
redesigning working components.

Status: Accepted

------------------------------------------------------------------------

## ADR-008

### Decision

Prefer complete implementations over placeholders.

Reason

Incomplete code slows development and confuses future contributors.

Status: Accepted

------------------------------------------------------------------------

# Future ADRs

Additional decisions should be recorded rather than being lost in commit
history.

Every significant architectural change requires a new ADR.
