# ADR-024: Use exactly three clues on fixed-child PuzzleBook Theme pages

## Status

Accepted for Commit 12.7.

## Context

A child usability test of a German Tennis PuzzleBook showed that fixed-child Theme pages were harder to use than intended. Page 1 already fixes the child order, so later Theme pages solve only the current Theme values. Keeping the larger standalone clue budget made those pages look crowded and obscured the simpler Theme-only task.

## Decision

Fixed-child PuzzleBook Theme pages always render exactly three visible clues. The composition follows the selected Difficulty:

- Easy: 2 direct Theme assignments + 1 relative Theme clue.
- Medium: 1 direct Theme assignment + 2 relative Theme clues.
- Hard: 0 direct Theme assignments + 3 relative Theme clues.

Generation retries when it cannot find a uniquely solvable exactly-three-clue candidate with the required composition. It does not widen the clue count, change Difficulty, or weaken numeric relative-clue quality.

Standalone themed puzzles remain variable-clue puzzles that solve both child order and Theme values using the existing `4! × 4!` search model.

PuzzleBook Theme pages also show both an empty Name row and the localized Theme-value row. The Name row is a usability aid for copying Page-1 names and does not change inherited fixed-child semantics. Each logical PuzzleBook puzzle page remains one physical PDF page so localized `Page x / y` footers match the actual generated page count.

## Consequences

The fixed-child worksheet is more compact and predictable for children. Difficulty remains based on direct revealed Theme cells, while page length is now a separate fixed worksheet contract for PuzzleBooks only.
