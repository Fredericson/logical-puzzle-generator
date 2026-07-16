# ADR-026: Plan PuzzleBook Difficulty per page

## Status

Accepted.

## Context

PuzzleBooks previously used one concrete Difficulty for the Position page and every fixed-child Theme page. Commit 13.0 adds a mixed request mode while preserving the established Easy, Medium, and Hard page-local semantics.

## Decision

- Use one public Difficulty parameter for the complete PuzzleBook.
- Preserve uniform Easy, Medium, and Hard PuzzleBooks.
- Add `mixed` as a PuzzleBook-only generation request mode.
- In mixed mode, include the Position page in the balanced page plan.
- Exclude the Summary page because it is not a puzzle page.
- Resolve a balanced deterministic Difficulty sequence before puzzle generation starts.
- Store only concrete Easy, Medium, or Hard Difficulty metadata on generated pages.
- Keep fixed-child Theme pages at exactly three clues.
- Preserve fixed-child Theme-page semantics: Easy has two direct Theme assignments, Medium has one, and Hard has zero.
- Limit runs to at most two consecutive puzzle pages with the same Difficulty.
- Establish one base seed and derive isolated deterministic streams, whether the base is supplied directly or obtained from a supplied random source.
- Isolate Difficulty planning randomness from category and puzzle generation.
- Do not implement adaptive, progressive, percentage-based, category-specific, or user-authored Difficulty sequences.

## Consequences

`mixed` is not a page-level Difficulty. The immutable plan is resolved once for the book-generation attempt. Page-local random streams keep retries from shifting later pages while each page keeps its resolved concrete Difficulty.
