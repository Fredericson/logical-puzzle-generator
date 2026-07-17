from __future__ import annotations

from collections import Counter
from io import BytesIO
import inspect
import random
import re

import pytest

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable, PageBreak

from logical_puzzle_generator.create_puzzle_book import create_puzzle_book
from logical_puzzle_generator.generator.puzzle_book import PuzzleBookGenerator
from logical_puzzle_generator.generator.puzzle_generator import PuzzleGenerator
from logical_puzzle_generator.pdf.generator import PdfGenerator
from logical_puzzle_generator.pdf.illustrations import (
    FourSlotIllustration,
    IllustrationDescriptor,
    IllustrationSlot,
    PuzzleIllustrationContext,
    PuzzleIllustrationRegistry,
    PuzzleIllustrationRenderer,
    PuzzlePageKind,
    TennisPositionIllustrationRenderer,
)
from logical_puzzle_generator.random_streams import derived_random
from logical_puzzle_generator.themes.tennis import create_template
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY


def test_every_tennis_category_has_category_specific_renderer() -> None:
    registry = PuzzleIllustrationRegistry()
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")

    missing = [
        c.id
        for c in theme.categories
        if not registry.has_category_specific_renderer("tennis_training", c.id)
    ]

    assert missing == []


def test_tennis_position_renderer_and_fallback_resolve() -> None:
    registry = PuzzleIllustrationRegistry()

    assert isinstance(
        registry.renderer_for("tennis_training", PuzzlePageKind.POSITION),
        TennisPositionIllustrationRenderer,
    )
    assert (
        registry.renderer_for("beach_day", PuzzlePageKind.POSITION).renderer_name
        == "generic_position"
    )


def test_tennis_renderers_have_four_ordered_non_overlapping_slots() -> None:
    registry = PuzzleIllustrationRegistry()
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    for category in theme.categories:
        context = PuzzleIllustrationContext(
            "tennis_training", PuzzlePageKind.THEME, category.id, base_seed=42
        )
        descriptor = registry.renderer_for(
            "tennis_training", PuzzlePageKind.THEME, category.id
        ).descriptor(context, width=480, height=100)
        assert len(descriptor.slots) == 4
        assert [slot.index for slot in descriptor.slots] == [1, 2, 3, 4]
        assert all(a.right < b.x for a, b in zip(descriptor.slots, descriptor.slots[1:]))
        assert descriptor.slots[-1].right <= 480.01
        assert all(slot.height <= 100 for slot in descriptor.slots)


def test_illustration_renderer_api_does_not_accept_solution() -> None:
    signature = inspect.signature(PuzzleIllustrationRenderer.build)

    assert "solution" not in signature.parameters
    assert tuple(signature.parameters) == ("self", "context", "width", "height")


def test_illustration_seed_is_deterministic_and_can_vary() -> None:
    registry = PuzzleIllustrationRegistry()
    renderer = registry.renderer_for("tennis_training", PuzzlePageKind.THEME, "bag_colour")
    context = PuzzleIllustrationContext(
        "tennis_training",
        PuzzlePageKind.THEME,
        "bag_colour",
        stream_namespace="puzzle_book.pdf.theme_page.1.bag_colour",
        base_seed=42,
    )
    same = PuzzleIllustrationContext(
        "tennis_training",
        PuzzlePageKind.THEME,
        "bag_colour",
        stream_namespace="puzzle_book.pdf.theme_page.1.bag_colour",
        base_seed=42,
    )
    different = PuzzleIllustrationContext(
        "tennis_training",
        PuzzlePageKind.THEME,
        "bag_colour",
        stream_namespace="puzzle_book.pdf.theme_page.1.bag_colour",
        base_seed=43,
    )

    assert (
        renderer.descriptor(context, width=480, height=100).variants
        == renderer.descriptor(same, width=480, height=100).variants
    )
    assert (
        renderer.descriptor(context, width=480, height=100).variants
        != renderer.descriptor(different, width=480, height=100).variants
    )


def test_different_categories_use_different_renderers() -> None:
    registry = PuzzleIllustrationRegistry()
    names = {
        category: registry.renderer_for(
            "tennis_training", PuzzlePageKind.THEME, category
        ).renderer_name
        for category in ("bag_colour", "racket_colour", "forehand_grip", "footwork")
    }

    assert len(set(names.values())) == len(names)


def test_puzzle_book_story_contains_position_and_category_illustrations(
    monkeypatch, tmp_path
) -> None:
    book = PuzzleBookGenerator(theme="tennis_training", seed=42, difficulty="easy").generate(
        theme_page_count=3
    )
    captured = {}

    def capture_build(self, output_path, story, *, page_count=None):
        captured[output_path.name] = story

    monkeypatch.setattr(PdfGenerator, "_build", capture_build)
    PdfGenerator(language="en").create_puzzle_book_pdf(book, tmp_path / "book.pdf")

    descriptors = [
        getattr(flowable, "descriptor", None)
        for flowable in captured["book.pdf"]
        if isinstance(flowable, Flowable)
    ]
    names = [descriptor.renderer_name for descriptor in descriptors if descriptor is not None]
    assert names[0] == "tennis_position"
    assert names[1:] == [
        PuzzleIllustrationRegistry()
        .renderer_for("tennis_training", PuzzlePageKind.THEME, puzzle.metadata.theme_category_id)
        .renderer_name
        for puzzle in book.theme_puzzles
    ]
    assert "tennis_bags" not in names[:1]
    assert sum(isinstance(flowable, PageBreak) for flowable in captured["book.pdf"]) == 4


def _assert_slot_geometry(descriptor, requested_width: float, requested_height: float) -> None:
    assert len(descriptor.slots) == 4
    assert [slot.index for slot in descriptor.slots] == [1, 2, 3, 4]
    for slot in descriptor.slots:
        assert slot.width > 0
        assert slot.height > 0
        assert slot.x >= 0
        assert slot.y >= 0
        assert slot.right <= requested_width + 0.01
        assert slot.y + slot.height <= requested_height + 0.01
        assert slot.y + 4 <= slot.y + slot.height
    for left, right in zip(descriptor.slots, descriptor.slots[1:]):
        assert left.right < right.x


def test_all_tennis_renderer_geometry_and_flowable_bounds_at_supported_sizes() -> None:
    registry = PuzzleIllustrationRegistry()
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    sizes = ((6.65 * inch, 1.30 * inch), (240.0, 72.0))
    contexts = [PuzzleIllustrationContext("tennis_training", PuzzlePageKind.POSITION, base_seed=42)]
    contexts.extend(
        PuzzleIllustrationContext(
            "tennis_training", PuzzlePageKind.THEME, category.id, base_seed=42
        )
        for category in theme.categories
    )

    for context in contexts:
        renderer = registry.renderer_for(
            context.theme_id, context.page_kind, context.theme_category_id
        )
        for width, height in sizes:
            descriptor = renderer.descriptor(context, width=width, height=height)
            flowable = renderer.build(context, width=width, height=height)
            _assert_slot_geometry(descriptor, width, height)
            assert flowable.width <= width
            assert flowable.height <= height


def test_tennis_renderer_coverage_matches_registry_exactly() -> None:
    registry = PuzzleIllustrationRegistry()
    theme_category_ids = {
        category.id for category in DEFAULT_THEME_REGISTRY.resolve("tennis_training").categories
    }
    exact_renderer_ids = {
        category_id
        for category_id in theme_category_ids
        if registry.has_category_specific_renderer("tennis_training", category_id)
    }

    assert exact_renderer_ids == theme_category_ids


def test_related_tennis_categories_have_distinct_visual_signatures() -> None:
    registry = PuzzleIllustrationRegistry()
    categories = (
        "bag_colour",
        "racket_count",
        "racket_colour",
        "string_colour",
        "forehand_grip",
        "backhand_type",
        "playing_style",
        "footwork",
    )
    signatures = {
        category: registry.renderer_for("tennis_training", PuzzlePageKind.THEME, category)
        .descriptor(
            PuzzleIllustrationContext(
                "tennis_training", PuzzlePageKind.THEME, category, base_seed=42
            ),
            width=6.65 * inch,
            height=1.30 * inch,
        )
        .visual_signature
        for category in categories
    }

    assert len(set(signatures.values())) == len(categories)


def test_forehand_grip_local_rotation_restores_canvas_state_and_geometry() -> None:
    registry = PuzzleIllustrationRegistry()
    renderer = registry.renderer_for("tennis_training", PuzzlePageKind.THEME, "forehand_grip")
    context = PuzzleIllustrationContext(
        "tennis_training",
        PuzzlePageKind.THEME,
        "forehand_grip",
        stream_namespace="puzzle_book.pdf.theme_page.3.forehand_grip",
        base_seed=42,
    )
    first = renderer.descriptor(context, width=6.65 * inch, height=1.30 * inch)
    second = renderer.descriptor(context, width=6.65 * inch, height=1.30 * inch)
    canvas = Canvas(BytesIO())
    initial_matrix = tuple(canvas._currentMatrix)

    renderer.build(context, width=6.65 * inch, height=1.30 * inch).drawOn(canvas, 0, 0)

    assert first == second
    _assert_slot_geometry(first, 6.65 * inch, 1.30 * inch)
    assert tuple(canvas._currentMatrix) == initial_matrix


def test_fallback_renderers_build_valid_flowables() -> None:
    registry = PuzzleIllustrationRegistry()
    position_renderer = registry.renderer_for("beach_day", PuzzlePageKind.POSITION)
    global_theme_renderer = registry.renderer_for("beach_day", PuzzlePageKind.THEME, "unknown")
    theme_fallback_renderer = registry.renderer_for(
        "tennis_training", PuzzlePageKind.THEME, "unknown"
    )

    assert position_renderer.renderer_name == "generic_position"
    assert global_theme_renderer.renderer_name == "generic_theme"
    assert theme_fallback_renderer.renderer_name == "tennis_generic_theme"
    for renderer, context in (
        (position_renderer, PuzzleIllustrationContext("beach_day", PuzzlePageKind.POSITION)),
        (
            global_theme_renderer,
            PuzzleIllustrationContext("beach_day", PuzzlePageKind.THEME, "unknown"),
        ),
        (
            theme_fallback_renderer,
            PuzzleIllustrationContext("tennis_training", PuzzlePageKind.THEME, "unknown"),
        ),
    ):
        flowable = renderer.build(context, width=240, height=72)
        assert flowable.width <= 240
        assert flowable.height <= 72


def _measure_story(story, available_width=6.65 * inch, available_height=1000):
    y = 0.0
    measurements = []
    for flowable in story:
        width, height = flowable.wrap(available_width, available_height)
        space_before = getattr(flowable, "getSpaceBefore", lambda: 0)()
        space_after = getattr(flowable, "getSpaceAfter", lambda: 0)()
        total_height = height + space_before + space_after
        measurements.append((flowable, y, y + total_height, width, total_height))
        y += total_height
    return measurements


def _controlled_category_puzzle(category_id: str, seed: int):
    return PuzzleGenerator(
        random_source=random.Random(seed),
        difficulty="easy",
        theme="tennis_training",
        category=category_id,
    ).generate(create_template())


def _controlled_story(pdf: PdfGenerator, category_id: str, language: str, page_index: int):
    theme = DEFAULT_THEME_REGISTRY.resolve("tennis_training")
    question = theme.category_by_id(category_id).localized_label(language)
    context = PuzzleIllustrationContext(
        "tennis_training",
        PuzzlePageKind.THEME,
        category_id,
        stream_namespace=f"puzzle_book.pdf.theme_page.{page_index}.{category_id}",
        base_seed=pdf._illustration_base_seed,
    )
    return (
        pdf._worksheet_story(
            _controlled_category_puzzle(category_id, seed=200 + page_index),
            theme_title=theme.localized_title(language),
            question=question,
            instruction=pdf._catalog.label("theme_page_reminder"),
            show_available_names=False,
            show_theme_values=True,
            show_child_field=True,
            show_theme_field=True,
            child_field_heading=pdf._catalog.label("name"),
            theme_field_heading=question,
            illustration_context=context,
        ),
        question,
    )


def test_long_question_headers_are_measured_and_render_as_single_pages(tmp_path) -> None:
    categories = ("racket_count", "favourite_surface", "forehand_grip", "tournament_wins")
    frame_height = A4[1] - (0.55 * inch * 2)
    frame_width = A4[0] - (0.8 * inch * 2)
    for language in ("en", "de"):
        pdf = PdfGenerator(
            language=language,
            random_source=derived_random(42, "puzzle_book.pdf.text"),
            illustration_random_source=derived_random(42, "puzzle_book.pdf.illustrations"),
        )
        for page_index, category_id in enumerate(categories, start=1):
            story, question = _controlled_story(pdf, category_id, language, page_index)
            measurements = _measure_story(
                story, available_width=frame_width, available_height=frame_height
            )
            illustration_index = next(
                index
                for index, (flowable, *_rest) in enumerate(measurements)
                if hasattr(flowable, "descriptor")
            )
            before_illustration = measurements[:illustration_index]
            illustration = measurements[illustration_index]

            assert question in story[0].text or question in story[1].text
            assert all(height > 0 for *_unused, height in before_illustration)
            preceding_spacer = before_illustration[-1]
            prior_content = before_illustration[-2]
            assert preceding_spacer[0].__class__.__name__ == "Spacer"
            assert preceding_spacer[4] > 0
            assert prior_content[2] < illustration[1]
            assert illustration[4] > 0
            assert measurements[-1][2] <= frame_height

            output_path = tmp_path / f"{language}_{category_id}.pdf"
            pdf._build(output_path, story)
            assert _pdf_page_marker_count(output_path) == 1


def _pdf_page_marker_count(path) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", path.read_bytes()))


def test_puzzle_book_pdf_page_counts_for_small_and_full_books(tmp_path) -> None:
    small = create_puzzle_book(
        theme_page_count=2,
        theme="tennis_training",
        seed=42,
        puzzle_path=tmp_path / "small.pdf",
        solution_path=tmp_path / "small_solution.pdf",
    )
    full = create_puzzle_book(
        theme_page_count=14,
        theme="tennis_training",
        seed=42,
        puzzle_path=tmp_path / "full.pdf",
        solution_path=tmp_path / "full_solution.pdf",
    )

    assert Counter(p.metadata.difficulty for p in small.pages if p.metadata) == Counter(
        {1: 1, 2: 1, 3: 1}
    )
    assert Counter(p.metadata.difficulty for p in full.pages if p.metadata) == Counter(
        {1: 5, 2: 5, 3: 5}
    )
    assert _pdf_page_marker_count(tmp_path / "small.pdf") == 4
    assert _pdf_page_marker_count(tmp_path / "small_solution.pdf") == 1
    assert _pdf_page_marker_count(tmp_path / "full.pdf") == 16
    assert _pdf_page_marker_count(tmp_path / "full_solution.pdf") == 1


def test_pdf_illustration_seed_does_not_mutate_puzzle_book_domain(tmp_path) -> None:
    book = PuzzleBookGenerator(theme="tennis_training", seed=42).generate(theme_page_count=2)

    def signature():
        return (
            tuple(child.name for child in book.children),
            tuple(puzzle.metadata.difficulty for puzzle in book.pages if puzzle.metadata),
            tuple(puzzle.metadata.theme_category_id for puzzle in book.theme_puzzles),
            book.summary_table,
        )

    before = signature()
    PdfGenerator(
        language="en", random_source=derived_random(1, "puzzle_book.pdf")
    ).create_puzzle_book_pdf(book, tmp_path / "a.pdf")
    middle = signature()
    PdfGenerator(
        language="en", random_source=derived_random(2, "puzzle_book.pdf")
    ).create_puzzle_book_pdf(book, tmp_path / "b.pdf")

    assert before == middle == signature()


def _rendered_clues(pdf: PdfGenerator, puzzle) -> tuple[str, ...]:
    return tuple(
        pdf._text_renderer.render_clues(
            puzzle.clues,
            item_count=len(puzzle.items),
            presentation_resolver=pdf._resolver(puzzle),
        )
    )


def _descriptor_from_pdf(pdf: PdfGenerator, category_id: str = "bag_colour"):
    context = PuzzleIllustrationContext(
        "tennis_training",
        PuzzlePageKind.THEME,
        category_id,
        stream_namespace=f"puzzle_book.pdf.theme_page.1.{category_id}",
        base_seed=pdf._illustration_base_seed,
    )
    return (
        PuzzleIllustrationRegistry()
        .renderer_for("tennis_training", PuzzlePageKind.THEME, category_id)
        .descriptor(context, width=6.65 * inch, height=1.30 * inch)
    )


def test_pdf_text_stream_is_independent_from_illustration_stream() -> None:
    puzzle = _controlled_category_puzzle("bag_colour", seed=500)
    first = PdfGenerator(
        random_source=derived_random(42, "puzzle_book.pdf.text"),
        illustration_random_source=derived_random(1, "puzzle_book.pdf.illustrations"),
    )
    second = PdfGenerator(
        random_source=derived_random(42, "puzzle_book.pdf.text"),
        illustration_random_source=derived_random(2, "puzzle_book.pdf.illustrations"),
    )

    assert _rendered_clues(first, puzzle) == _rendered_clues(second, puzzle)


def test_pdf_illustration_stream_is_independent_from_text_stream() -> None:
    first = PdfGenerator(
        random_source=derived_random(1, "puzzle_book.pdf.text"),
        illustration_random_source=derived_random(42, "puzzle_book.pdf.illustrations"),
    )
    second = PdfGenerator(
        random_source=derived_random(2, "puzzle_book.pdf.text"),
        illustration_random_source=derived_random(42, "puzzle_book.pdf.illustrations"),
    )

    assert _descriptor_from_pdf(first, "forehand_grip") == _descriptor_from_pdf(
        second, "forehand_grip"
    )


def test_illustration_consumption_does_not_shift_text() -> None:
    puzzle = _controlled_category_puzzle("bag_colour", seed=501)
    with_extra_illustrations = PdfGenerator(
        random_source=derived_random(42, "puzzle_book.pdf.text"),
        illustration_random_source=derived_random(42, "puzzle_book.pdf.illustrations"),
    )
    immediate_text = PdfGenerator(
        random_source=derived_random(42, "puzzle_book.pdf.text"),
        illustration_random_source=derived_random(42, "puzzle_book.pdf.illustrations"),
    )
    for category_id in ("bag_colour", "forehand_grip", "racket_count"):
        _descriptor_from_pdf(with_extra_illustrations, category_id)

    assert _rendered_clues(with_extra_illustrations, puzzle) == _rendered_clues(
        immediate_text, puzzle
    )


def test_text_consumption_does_not_shift_illustrations() -> None:
    puzzle = _controlled_category_puzzle("bag_colour", seed=502)
    with_extra_text = PdfGenerator(
        random_source=derived_random(42, "puzzle_book.pdf.text"),
        illustration_random_source=derived_random(42, "puzzle_book.pdf.illustrations"),
    )
    immediate_illustration = PdfGenerator(
        random_source=derived_random(42, "puzzle_book.pdf.text"),
        illustration_random_source=derived_random(42, "puzzle_book.pdf.illustrations"),
    )
    _rendered_clues(with_extra_text, puzzle)
    _rendered_clues(with_extra_text, puzzle)

    assert _descriptor_from_pdf(with_extra_text, "forehand_grip") == _descriptor_from_pdf(
        immediate_illustration, "forehand_grip"
    )


def test_seeded_pdf_illustration_descriptors_are_deterministic_for_key_pages() -> None:
    first = PdfGenerator(
        random_source=derived_random(42, "puzzle_book.pdf.text"),
        illustration_random_source=derived_random(42, "puzzle_book.pdf.illustrations"),
    )
    second = PdfGenerator(
        random_source=derived_random(42, "puzzle_book.pdf.text"),
        illustration_random_source=derived_random(42, "puzzle_book.pdf.illustrations"),
    )
    registry = PuzzleIllustrationRegistry()
    contexts = (
        PuzzleIllustrationContext(
            "tennis_training", PuzzlePageKind.POSITION, base_seed=first._illustration_base_seed
        ),
        PuzzleIllustrationContext(
            "tennis_training",
            PuzzlePageKind.THEME,
            "bag_colour",
            base_seed=first._illustration_base_seed,
        ),
        PuzzleIllustrationContext(
            "tennis_training",
            PuzzlePageKind.THEME,
            "forehand_grip",
            base_seed=first._illustration_base_seed,
        ),
    )
    second_contexts = tuple(
        PuzzleIllustrationContext(
            context.theme_id,
            context.page_kind,
            context.theme_category_id,
            context.stream_namespace,
            second._illustration_base_seed,
        )
        for context in contexts
    )

    for context, second_context in zip(contexts, second_contexts, strict=True):
        renderer = registry.renderer_for(
            context.theme_id, context.page_kind, context.theme_category_id
        )
        assert renderer.descriptor(context, width=480, height=100) == renderer.descriptor(
            second_context, width=480, height=100
        )


def test_unseeded_illustration_base_seed_is_established_from_illustration_source() -> None:
    first = PdfGenerator(illustration_random_source=random.Random(1))
    second = PdfGenerator(illustration_random_source=random.Random(2))

    assert first._illustration_base_seed != second._illustration_base_seed
    assert (
        _descriptor_from_pdf(first, "bag_colour").variants
        != _descriptor_from_pdf(second, "bag_colour").variants
    )


def test_unseeded_illustration_base_seed_uses_system_random_once(monkeypatch) -> None:
    calls = []

    class FakeSystemRandom:
        def getrandbits(self, bits):
            calls.append(bits)
            return 123456789

    monkeypatch.setattr(
        "logical_puzzle_generator.pdf.generator.random.SystemRandom", FakeSystemRandom
    )

    pdf = PdfGenerator()

    assert pdf._illustration_base_seed == 123456789
    assert calls == [64]


def test_rejects_conflicting_illustration_seed_inputs() -> None:
    with pytest.raises(ValueError, match="illustration_seed"):
        PdfGenerator(illustration_seed=1, illustration_random_source=random.Random(1))


def test_four_slot_illustration_restores_outer_canvas_state_on_exception() -> None:
    descriptor = IllustrationDescriptor(
        renderer_name="broken",
        context=PuzzleIllustrationContext(
            "tennis_training", PuzzlePageKind.THEME, "broken", base_seed=1
        ),
        slots=(IllustrationSlot(1, 0, 0, 20, 20),),
        variants=(0,),
        concept="broken renderer",
        symbol_family="broken",
        requested_width=20,
        requested_height=20,
    )

    def raise_from_slot(canvas, slot, variant):
        canvas.translate(5, 5)
        raise RuntimeError("intentional slot failure")

    flowable = FourSlotIllustration(descriptor, raise_from_slot)
    canvas = Canvas(BytesIO())
    initial_matrix = tuple(canvas._currentMatrix)
    initial_stack_depth = len(canvas.state_stack)
    flowable.canv = canvas

    with pytest.raises(RuntimeError, match="intentional slot failure"):
        flowable.draw()

    assert tuple(canvas._currentMatrix) == initial_matrix
    assert len(canvas.state_stack) == initial_stack_depth
    canvas.line(0, 0, 1, 1)
