# ADR-027: Render PuzzleBook illustrations from page context

## Status

Accepted.

## Context

PuzzleBook pages need child-facing drawings that match the page role without changing puzzle generation. The Position page establishes child order, while each Theme page asks about one Theme category. The previous presentation reused the same generic lineup artwork too broadly.

## Decision

PuzzleBook illustration selection belongs to the PDF presentation layer. The renderer receives a `PuzzleIllustrationContext` containing only the Theme ID, page kind, optional Theme-category ID, stable PDF stream namespace, and optional base seed. It does not receive child names, selected values, solutions, constraints, or solver data.

Position pages resolve by exact Theme renderer and then a global four-child fallback. Theme pages resolve by exact Theme/category renderer, then Theme-generic fallback, then global generic fallback. Tennis now has a dedicated Position renderer and category-specific renderers for every registered Tennis category.

Drawings use ReportLab vector primitives. Controlled visual variation uses a PDF illustration stream that is separate from clue-text randomness. Seeded books derive `puzzle_book.pdf.text` for wording and `puzzle_book.pdf.illustrations` for illustration base-seed establishment; page variants then derive with `puzzle_book.pdf.position` and `puzzle_book.pdf.theme_page.<page_index>.<category_id>` using the stable seed helper rather than Python `hash()`. Unseeded PDF rendering establishes one non-deterministic illustration base seed per `PdfGenerator`.

PuzzleBook headers rely on naturally measured ReportLab paragraphs and flowables; illustrations are inserted as separate flowables below the header and instruction area, so long localized Question labels do not overlap artwork. Layout regressions render actual pages rather than only checking abstract descriptors.

PuzzleBooks default to Mixed Difficulty when omitted or when the programmatic input is `None`. Standalone puzzle default Difficulty behaviour remains unchanged.

## Consequences

The domain `Puzzle` and `PuzzleBook` models stay independent from ReportLab drawing objects. Illustration changes cannot affect constraints, clue selection, Difficulty planning, Summary rows, solver search spaces, or Theme value generation. Illustration rendering must not consume clue-text randomness. Outer and per-slot canvas state must be restored through `finally` so rotated handles, rackets, or future poses cannot affect later slots or labels.
