from __future__ import annotations

from dataclasses import dataclass

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable


@dataclass(frozen=True)
class LineupSlot:
    """Presentation data for one left-to-right puzzle position."""

    position: int
    x: float
    figure_width: float
    box_width: float
    box_height: float
    label: str = ""


class GirlFigureRenderer:
    """Draws anonymous, child-friendly vector girl placeholders."""

    DRESSES = (colors.pink, colors.lightblue, colors.lavender, colors.lightgreen)
    HAIR = (colors.saddlebrown, colors.black, colors.darkgoldenrod, colors.brown)

    def draw(
        self, canvas: Canvas, x: float, y: float, width: float, height: float, variant: int
    ) -> None:
        center = x + width / 2
        skin = colors.Color(0.96, 0.78, 0.62)
        dress = self.DRESSES[variant % len(self.DRESSES)]
        hair = self.HAIR[variant % len(self.HAIR)]

        canvas.saveState()
        canvas.setStrokeColor(colors.darkslategray)
        canvas.setLineWidth(1.4)

        # Legs and shoes.
        canvas.setStrokeColor(colors.Color(0.35, 0.25, 0.2))
        canvas.line(center - 10, y + 16, center - 16, y)
        canvas.line(center + 10, y + 16, center + 16, y)
        canvas.setFillColor(colors.white)
        canvas.ellipse(center - 24, y - 3, center - 10, y + 3, fill=1)
        canvas.ellipse(center + 10, y - 3, center + 24, y + 3, fill=1)

        # Dress/body.
        canvas.setFillColor(dress)
        body = canvas.beginPath()
        body.moveTo(center, y + 82)
        body.lineTo(center - 30, y + 20)
        body.lineTo(center + 30, y + 20)
        body.close()
        canvas.drawPath(body, fill=1, stroke=1)

        # Arms.
        canvas.setStrokeColor(skin)
        canvas.setLineWidth(5)
        canvas.line(center - 19, y + 62, center - 42, y + 36)
        canvas.line(center + 19, y + 62, center + 42, y + 50)

        # Optional tennis racket for friendly theme, never item-specific.
        if variant % 2 == 0:
            canvas.setStrokeColor(colors.darkslategray)
            canvas.setLineWidth(1.2)
            canvas.line(center + 42, y + 50, center + 57, y + 30)
            canvas.ellipse(center + 50, y + 50, center + 76, y + 78, fill=0)
            canvas.line(center + 56, y + 53, center + 70, y + 75)
            canvas.line(center + 70, y + 53, center + 56, y + 75)

        # Head, hair, and simple face.
        canvas.setStrokeColor(colors.darkslategray)
        canvas.setLineWidth(1.2)
        canvas.setFillColor(skin)
        canvas.circle(center, y + 103, 22, fill=1)
        canvas.setFillColor(hair)
        canvas.wedge(center - 24, y + 94, center + 24, y + 130, 0, 180, fill=1, stroke=0)
        if variant == 1:
            canvas.circle(center - 24, y + 96, 8, fill=1, stroke=0)
            canvas.circle(center + 24, y + 96, 8, fill=1, stroke=0)
        elif variant == 2:
            canvas.rect(center - 26, y + 105, 52, 10, fill=1, stroke=0)

        canvas.setFillColor(colors.black)
        canvas.circle(center - 7, y + 103, 1.6, fill=1)
        canvas.circle(center + 7, y + 103, 1.6, fill=1)
        canvas.arc(center - 7, y + 92, center + 7, y + 100, 200, 140)
        canvas.restoreState()


class PlayerLineupRenderer(Flowable):
    """ReportLab flowable for a horizontal position lineup with writable boxes."""

    def __init__(
        self,
        item_count: int,
        labels: list[str] | None = None,
        instruction: str = "",
        width: float = 6.65 * inch,
    ) -> None:
        super().__init__()
        if item_count < 1:
            raise ValueError("Lineup requires at least one position.")
        self.item_count = item_count
        self.labels = labels if labels is not None else [""] * item_count
        if len(self.labels) != item_count:
            raise ValueError("Lineup label count must match item count.")
        self.instruction = instruction
        self.width = width
        self.height = 3.28 * inch
        self._figure_renderer = GirlFigureRenderer()

    def layout_slots(self) -> list[LineupSlot]:
        slot_width = self.width / self.item_count
        figure_width = min(1.26 * inch, slot_width * 0.7)
        box_width = min(1.48 * inch, slot_width * 0.88)
        box_height = 0.5 * inch
        return [
            LineupSlot(
                position=index + 1,
                x=index * slot_width + slot_width / 2,
                figure_width=figure_width,
                box_width=box_width,
                box_height=box_height,
                label=self.labels[index],
            )
            for index in range(self.item_count)
        ]

    def draw(self) -> None:
        canvas = self.canv
        canvas.saveState()
        if self.instruction:
            canvas.setFont("Helvetica-Bold", 12.5)
            canvas.setFillColor(colors.black)
            canvas.drawString(0, self.height - 12, self.instruction)

        figure_bottom = 1.14 * inch
        figure_height = 1.6 * inch
        box_y = 0.4 * inch
        for index, slot in enumerate(self.layout_slots()):
            center = slot.x
            self._figure_renderer.draw(
                canvas,
                center - slot.figure_width / 2,
                figure_bottom,
                slot.figure_width,
                figure_height,
                index,
            )
            box_x = center - slot.box_width / 2
            canvas.setStrokeColor(colors.black)
            canvas.setLineWidth(1.4)
            canvas.setFillColor(colors.white)
            canvas.rect(box_x, box_y, slot.box_width, slot.box_height, fill=1, stroke=1)
            if slot.label:
                canvas.setFillColor(colors.black)
                canvas.setFont("Helvetica-Bold", 12.5)
                canvas.drawCentredString(center, box_y + slot.box_height / 2 - 4.5, slot.label)
            canvas.setFillColor(colors.black)
            canvas.setFont("Helvetica-Bold", 11)
            canvas.drawCentredString(center, 0.08 * inch, str(slot.position))
        canvas.restoreState()
