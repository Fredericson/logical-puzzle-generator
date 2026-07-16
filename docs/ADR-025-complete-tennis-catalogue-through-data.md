# ADR-025: Complete the Tennis Training category catalogue through data

## Status

Accepted.

## Context

The Tennis Training Theme needed the remaining planned child-facing categories while preserving the one-category-per-page model, standalone `4! × 4!` solving, fixed-child PuzzleBook Theme pages, and category exhaustion before repetition. Several values require grammar-sensitive English or German wording, including colour adjective endings, plural strings, established Tennis grip names, respectful body-build descriptions, and accessory articles.

## Decision

Add `racket_colour`, `string_colour`, `forehand_grip`, `lucky_charm`, `footwork`, `body_build`, and `accessory` as normal `ThemeCategoryDefinition` registry entries under `tennis_training`.

Use value-level localized presentation data for short labels, direct clue labels, subject phrases, position subject phrases, and natural position-anchor sentences where needed. Complete position-anchor sentences are narrow optional overrides used only when generic subject-based rendering is insufficient for plural agreement, idiomatic wording, or irregular articles. The renderer remains generic: it resolves presentation from the active `ThemeCategoryInstance` using position-anchor override → position subject phrase → subject phrase → full label, and does not branch on Tennis category IDs.

All new categories participate in standalone puzzle generation and PuzzleBook generation through the existing registry and category-instance flow. PuzzleBooks continue to select every registered category before repetition, and repeated pages continue to receive distinct instance IDs and visible numbering through existing summary/page-label presentation.

## Consequences

The Tennis catalogue can grow through data additions without adding solver, validator, PuzzleBook, PDF, or clue-renderer special cases. Categories with more than four values sample four distinct values per page, while categories with exactly four values use all four. The new categories reuse existing direct-assignment and spatial constraints; no new arithmetic or Tennis-specific constraint type is introduced. All production values receive direct, relative, and position rendering coverage so grammar-sensitive data defects are caught at the registry boundary.

## Commit 12.9 amendment

Commit 12.9 keeps the ADR-025 architecture and strengthens its regression boundary. Catalogue values are now covered by controlled direct, relative, and position wording tests. Long-value layout tests must explicitly select the target values in the generated page instances before rendering so the PDF regression cannot pass by inspecting only registry contents. The earlier hair-ribbon lucky-charm draft is replaced by `friendship_bracelet` (`Friendship Bracelet` / `Freundschaftsarmband`). Grammar-sensitive wording remains registry data resolved by the generic presentation path, not category-specific renderer logic.
