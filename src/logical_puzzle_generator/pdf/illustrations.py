from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable

from logical_puzzle_generator.random_streams import derive_seed


class PuzzlePageKind(Enum):
    POSITION = "position"
    THEME = "theme"


@dataclass(frozen=True, slots=True)
class PuzzleIllustrationContext:
    theme_id: str
    page_kind: PuzzlePageKind
    theme_category_id: str | None = None
    stream_namespace: str = "puzzle_book.pdf"
    base_seed: int | None = None


@dataclass(frozen=True, slots=True)
class IllustrationSlot:
    index: int
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width


@dataclass(frozen=True, slots=True)
class IllustrationDescriptor:
    renderer_name: str
    context: PuzzleIllustrationContext
    slots: tuple[IllustrationSlot, ...]
    variants: tuple[int, ...]
    concept: str
    symbol_family: str
    requested_width: float
    requested_height: float

    @property
    def visual_signature(self) -> tuple[str, str, str, int]:
        return (self.renderer_name, self.concept, self.symbol_family, len(self.slots))


class PuzzleIllustrationRenderer(Protocol):
    renderer_name: str
    concept: str

    def descriptor(
        self, context: PuzzleIllustrationContext, *, width: float, height: float
    ) -> IllustrationDescriptor: ...
    def build(
        self, context: PuzzleIllustrationContext, *, width: float, height: float
    ) -> Flowable: ...


class FourSlotIllustration(Flowable):
    def __init__(
        self,
        descriptor: IllustrationDescriptor,
        draw_slot: Callable[[Canvas, IllustrationSlot, int], None],
    ) -> None:
        super().__init__()
        self.descriptor = descriptor
        self.width = descriptor.requested_width
        self.height = descriptor.requested_height
        self._draw_slot = draw_slot

    def draw(self) -> None:
        c = self.canv
        c.saveState()
        try:
            for slot, variant in zip(self.descriptor.slots, self.descriptor.variants, strict=True):
                c.saveState()
                try:
                    c.setStrokeColor(colors.darkslategray)
                    c.setLineWidth(1)
                    c.setFillColor(colors.whitesmoke)
                    c.roundRect(slot.x, slot.y, slot.width, slot.height, 8, fill=1, stroke=1)
                    self._draw_slot(c, slot, variant)
                    c.setFillColor(colors.black)
                    c.setFont("Helvetica-Bold", 10)
                    c.drawCentredString(slot.x + slot.width / 2, slot.y + 4, str(slot.index))
                finally:
                    c.restoreState()
        finally:
            c.restoreState()


def _slots(width: float, height: float) -> tuple[IllustrationSlot, ...]:
    gap = 0.08 * inch
    slot_w = (width - gap * 3) / 4
    slot_h = height - 0.18 * inch
    return tuple(
        IllustrationSlot(i + 1, i * (slot_w + gap), 0.10 * inch, slot_w, slot_h) for i in range(4)
    )


def _variants(context: PuzzleIllustrationContext, count: int = 4) -> tuple[int, ...]:
    base_seed = (
        context.base_seed
        if context.base_seed is not None
        else random.SystemRandom().getrandbits(64)
    )
    rng = random.Random(derive_seed(base_seed, context.stream_namespace))
    return tuple(rng.randrange(6) for _ in range(count))


class SymbolIllustrationRenderer:
    def __init__(self, renderer_name: str, concept: str, symbol: str) -> None:
        self.renderer_name = renderer_name
        self.concept = concept
        self.symbol = symbol

    def descriptor(
        self, context: PuzzleIllustrationContext, *, width: float, height: float
    ) -> IllustrationDescriptor:
        return IllustrationDescriptor(
            self.renderer_name,
            context,
            _slots(width, height),
            _variants(context),
            self.concept,
            self.symbol,
            width,
            height,
        )

    def build(self, context: PuzzleIllustrationContext, *, width: float, height: float) -> Flowable:
        return FourSlotIllustration(
            self.descriptor(context, width=width, height=height), self._draw_slot
        )

    def _draw_slot(self, c: Canvas, s: IllustrationSlot, v: int) -> None:
        cx, cy = s.x + s.width / 2, s.y + s.height / 2 + 4
        c.saveState()
        try:
            c.setStrokeColor(colors.black)
            c.setLineWidth(1.5)
            c.setFillColor(colors.white)
            if self.symbol == "bag":
                self._draw_tennis_bag(c, cx, cy, count_badge=False)
            elif self.symbol == "racket_count":
                self._draw_tennis_bag(c, cx, cy, count_badge=True)
            elif self.symbol == "racket":
                self._draw_racket(c, cx, cy, angle=(v - 2) * 5, strings=False)
            elif self.symbol == "strings":
                self._draw_racket(c, cx, cy + 2, angle=0, strings=True)
            elif self.symbol == "grip":
                self._draw_grip(c, cx, cy, angle=(v - 2) * 4)
            elif self.symbol == "player":
                self._draw_player(c, cx, cy, backhand=True)
            elif self.symbol == "training":
                c.line(cx - 30, cy - 22, cx + 30, cy - 22)
                c.rect(cx - 28, cy - 22, 12, 22, fill=0)
                c.circle(cx + 18, cy + 6, 10, fill=0)
                c.circle(cx + 30, cy - 12, 4, fill=0)
            elif self.symbol == "strategy":
                c.rect(cx - 32, cy - 24, 64, 48, fill=0)
                c.line(cx, cy - 24, cx, cy + 24)
                c.circle(cx - 20, cy - 4, 4, fill=1)
                c.circle(cx + 20, cy + 10, 4, fill=1)
                c.line(cx - 16, cy - 2, cx + 15, cy + 8)
                c.line(cx + 9, cy + 11, cx + 15, cy + 8)
                c.line(cx + 10, cy + 3, cx + 15, cy + 8)
            elif self.symbol == "surface":
                c.rect(cx - 30, cy - 24, 60, 48, fill=0)
                c.line(cx, cy - 24, cx, cy + 24)
                c.line(cx - 30, cy, cx + 30, cy)
                for i in range(5):
                    c.line(cx - 28, cy - 18 + i * 8, cx + 28, cy - 22 + i * 8)
            elif self.symbol == "trophy":
                c.rect(cx - 11, cy - 18, 22, 28, fill=0)
                c.arc(cx - 26, cy - 2, cx - 8, cy + 18, 270, 180)
                c.arc(cx + 8, cy - 2, cx + 26, cy + 18, 90, 180)
                c.rect(cx - 20, cy - 30, 40, 10, fill=0)
                c.rect(cx - 14, cy - 8, 28, 10, fill=0)
            elif self.symbol == "charm":
                c.roundRect(cx - 24, cy - 18, 48, 36, 7, fill=0)
                c.circle(cx, cy, 12, fill=0)
                c.circle(cx, cy + 18, 4, fill=0)
                c.line(cx - 7, cy, cx + 7, cy)
                c.line(cx, cy - 7, cx, cy + 7)
            elif self.symbol == "footwork":
                for i in range(4):
                    x = cx - 31 + i * 19
                    y = cy - 21 + (i % 2) * 18
                    c.ellipse(x, y, x + 14, y + 20, fill=0)
                    if i < 3:
                        c.line(x + 13, y + 10, x + 20, y + (20 if i % 2 == 0 else 0))
            elif self.symbol == "body":
                c.circle(cx, cy + 24, 10, fill=0)
                c.roundRect(cx - 12 - v, cy - 24, 24 + v * 2, 42, 10, fill=0)
            elif self.symbol == "accessory":
                c.circle(cx, cy + 5, 22, fill=0)
                c.arc(cx - 24, cy + 18, cx + 24, cy + 40, 0, 180)
                c.rect(cx - 24, cy + 20, 48, 5, fill=0)
                c.rect(cx - 16, cy - 2, 32, 8, fill=0)
            else:
                c.circle(cx, cy, 20, fill=0)
        finally:
            c.restoreState()

    def _draw_tennis_bag(self, c: Canvas, cx: float, cy: float, *, count_badge: bool) -> None:
        c.roundRect(cx - 28, cy - 15, 56, 34, 7, fill=1, stroke=1)
        c.arc(cx - 19, cy + 7, cx + 19, cy + 31, 0, 180)
        c.line(cx - 20, cy + 10, cx + 18, cy + 10)
        c.roundRect(cx + 6, cy - 8, 16, 14, 3, fill=0, stroke=1)
        if count_badge:
            for offset in (-10, 0, 10):
                c.line(cx + offset, cy + 20, cx + offset, cy + 34)
            c.circle(cx - 18, cy - 3, 7, fill=0)
        else:
            c.line(cx - 22, cy + 2, cx - 5, cy + 2)

    def _draw_racket(self, c: Canvas, cx: float, cy: float, *, angle: float, strings: bool) -> None:
        c.saveState()
        try:
            c.translate(cx, cy)
            c.rotate(angle)
            c.ellipse(-19, -4, 19, 38, fill=0, stroke=1)
            c.line(0, -28, 0, -4)
            if strings:
                for dx in (-12, -6, 0, 6, 12):
                    c.line(dx, 0, dx, 34)
                for dy in (4, 10, 16, 22, 28, 34):
                    c.line(-15, dy, 15, dy)
            else:
                c.line(-9, 8, 9, 25)
                c.line(-9, 25, 9, 8)
        finally:
            c.restoreState()

    def _draw_grip(self, c: Canvas, cx: float, cy: float, *, angle: float) -> None:
        c.saveState()
        try:
            c.translate(cx, cy)
            c.rotate(angle)
            c.roundRect(-9, -30, 18, 58, 5, fill=0, stroke=1)
            c.line(-6, -20, 6, -20)
            c.line(-6, -8, 6, -8)
            c.line(-6, 4, 6, 4)
            c.ellipse(-24, -7, 2, 17, fill=0, stroke=1)
            c.line(-17, -4, 13, 7)
        finally:
            c.restoreState()

    def _draw_player(self, c: Canvas, cx: float, cy: float, *, backhand: bool) -> None:
        c.circle(cx, cy + 24, 10, fill=0)
        c.line(cx, cy + 14, cx - 4, cy - 18)
        if backhand:
            c.line(cx - 2, cy + 5, cx - 28, cy + 14)
            c.line(cx - 28, cy + 14, cx - 38, cy + 24)
        else:
            c.line(cx, cy + 5, cx + 24, cy + 16)
        c.line(cx - 4, cy - 18, cx - 18, cy - 32)
        c.line(cx - 4, cy - 18, cx + 12, cy - 30)


class TennisPositionIllustrationRenderer(SymbolIllustrationRenderer):
    def __init__(self) -> None:
        super().__init__("tennis_position", "four anonymous girls on a tennis court", "position")

    def _draw_slot(self, c: Canvas, s: IllustrationSlot, v: int) -> None:
        cx, cy = s.x + s.width / 2, s.y + s.height / 2
        c.setStrokeColor(colors.darkgreen)
        c.line(s.x + 4, s.y + 12, s.right - 4, s.y + 12)
        c.line(s.x + 8, s.y + s.height - 20, s.right - 8, s.y + s.height - 20)
        c.line(cx, s.y + 12, cx, s.y + s.height - 20)
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        c.circle(cx, cy + 20, 10, fill=1)
        c.line(cx, cy + 10, cx, cy - 22)
        c.line(cx - 18, cy - 2, cx + 18, cy - 2)
        c.line(cx, cy - 22, cx - 12, cy - 42)
        c.line(cx, cy - 22, cx + 12, cy - 42)
        c.ellipse(cx + 14, cy + 1, cx + 34, cy + 24, fill=0)


TENNIS_CATEGORY_RENDERERS = {
    "training": SymbolIllustrationRenderer(
        "tennis_training_stations", "four tennis training stations", "training"
    ),
    "backhand_type": SymbolIllustrationRenderer(
        "tennis_backhand_players", "four neutral backhand player silhouettes", "player"
    ),
    "bag_colour": SymbolIllustrationRenderer("tennis_bags", "four neutral tennis bags", "bag"),
    "playing_style": SymbolIllustrationRenderer(
        "tennis_play_symbols", "four neutral court strategy symbols", "strategy"
    ),
    "favourite_surface": SymbolIllustrationRenderer(
        "tennis_surface_panels", "four neutral court-surface panels", "surface"
    ),
    "tournament_wins": SymbolIllustrationRenderer(
        "tennis_trophy_panels", "four trophy panels with empty fields", "trophy"
    ),
    "racket_count": SymbolIllustrationRenderer(
        "tennis_racket_count_bags", "four tennis bags with empty count boxes", "racket_count"
    ),
    "racket_colour": SymbolIllustrationRenderer(
        "tennis_rackets", "four neutral tennis racket outlines", "racket"
    ),
    "string_colour": SymbolIllustrationRenderer(
        "tennis_string_beds", "four racket string beds", "strings"
    ),
    "forehand_grip": SymbolIllustrationRenderer(
        "tennis_forehand_grips", "four simplified racket-handle grip diagrams", "grip"
    ),
    "lucky_charm": SymbolIllustrationRenderer(
        "tennis_lucky_charms", "four neutral lucky-charm panels", "charm"
    ),
    "footwork": SymbolIllustrationRenderer(
        "tennis_footwork", "four movement-step footprint panels", "footwork"
    ),
    "body_build": SymbolIllustrationRenderer(
        "tennis_body_silhouettes", "four respectful neutral child silhouettes", "body"
    ),
    "accessory": SymbolIllustrationRenderer(
        "tennis_accessories", "four neutral accessory panels", "accessory"
    ),
}


class PuzzleIllustrationRegistry:
    def __init__(self) -> None:
        self._position = {"tennis_training": TennisPositionIllustrationRenderer()}
        self._theme = {("tennis_training", k): v for k, v in TENNIS_CATEGORY_RENDERERS.items()}
        self._theme_fallback = {
            "tennis_training": SymbolIllustrationRenderer(
                "tennis_generic_theme", "four neutral tennis answer slots", "racket"
            )
        }
        self._generic_position = SymbolIllustrationRenderer(
            "generic_position", "four anonymous children in ordered slots", "player"
        )
        self._generic_theme = SymbolIllustrationRenderer(
            "generic_theme", "four neutral answer slots", "generic"
        )

    def renderer_for(
        self, theme_id: str, page_kind: PuzzlePageKind, theme_category_id: str | None = None
    ) -> PuzzleIllustrationRenderer:
        if page_kind is PuzzlePageKind.POSITION:
            return self._position.get(theme_id, self._generic_position)
        return self._theme.get(
            (theme_id, theme_category_id or ""),
            self._theme_fallback.get(theme_id, self._generic_theme),
        )

    def has_category_specific_renderer(self, theme_id: str, category_id: str) -> bool:
        return (theme_id, category_id) in self._theme
