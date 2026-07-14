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
    name_box_height: float
    theme_box_height: float
    name_label: str = ""
    theme_label: str = ""

    @property
    def box_height(self) -> float:
        return self.name_box_height

    @property
    def label(self) -> str:
        return self.name_label


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
        canvas.setStrokeColor(colors.Color(0.35, 0.25, 0.2))
        canvas.line(center - 10, y + 16, center - 16, y)
        canvas.line(center + 10, y + 16, center + 16, y)
        canvas.setFillColor(colors.white)
        canvas.ellipse(center - 24, y - 3, center - 10, y + 3, fill=1)
        canvas.ellipse(center + 10, y - 3, center + 24, y + 3, fill=1)
        canvas.setFillColor(dress)
        body = canvas.beginPath()
        body.moveTo(center, y + 82)
        body.lineTo(center - 30, y + 20)
        body.lineTo(center + 30, y + 20)
        body.close()
        canvas.drawPath(body, fill=1, stroke=1)
        canvas.setStrokeColor(skin)
        canvas.setLineWidth(5)
        canvas.line(center - 19, y + 62, center - 42, y + 36)
        canvas.line(center + 19, y + 62, center + 42, y + 50)
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
    """ReportLab flowable for a horizontal lineup with separate answer boxes."""

    def __init__(
        self,
        item_count: int,
        labels: list[str | tuple[str, str]] | None = None,
        instruction: str = "",
        width: float = 6.65 * inch,
        show_child_field: bool = True,
        show_theme_field: bool = True,
        child_field_heading: str = "",
        theme_field_heading: str = "",
    ) -> None:
        super().__init__()
        if item_count < 1:
            raise ValueError("Lineup requires at least one position.")
        self.item_count = item_count
        raw_labels = labels if labels is not None else [("", "")] * item_count
        self.labels = [(label, "") if isinstance(label, str) else label for label in raw_labels]
        if len(self.labels) != item_count:
            raise ValueError("Lineup label count must match item count.")
        self.instruction = instruction
        self.width = width
        self.show_child_field = show_child_field
        self.show_theme_field = show_theme_field
        if not self.show_child_field and not self.show_theme_field:
            raise ValueError("Lineup must show at least one answer field.")
        self.child_field_heading = child_field_heading
        self.theme_field_heading = theme_field_heading
        field_count = int(self.show_child_field) + int(self.show_theme_field)
        self.height = (3.16 + 0.35 * (field_count - 1)) * inch
        self._figure_renderer = GirlFigureRenderer()

    def layout_slots(self) -> list[LineupSlot]:
        slot_width = self.width / self.item_count
        figure_width = min(1.26 * inch, slot_width * 0.7)
        box_width = min(1.48 * inch, slot_width * 0.88)
        name_box_height = 0.5 * inch if self.show_child_field else 0
        theme_box_height = 0.5 * inch if self.show_theme_field else 0
        return [
            LineupSlot(
                position=index + 1,
                x=index * slot_width + slot_width / 2,
                figure_width=figure_width,
                box_width=box_width,
                name_box_height=name_box_height,
                theme_box_height=theme_box_height,
                name_label=self.labels[index][0],
                theme_label=self.labels[index][1],
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

        figure_bottom = 1.34 * inch
        figure_height = 1.52 * inch
        first_box_y = 0.34 * inch
        theme_box_y = first_box_y
        name_box_y = first_box_y + (0.58 * inch if self.show_theme_field else 0)
        if self.show_child_field and self.child_field_heading:
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(0, name_box_y + 0.53 * inch, self.child_field_heading)
        if self.show_theme_field and self.theme_field_heading:
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(0, theme_box_y + 0.53 * inch, self.theme_field_heading)
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
            if self.show_child_field:
                self._draw_box(
                    canvas,
                    box_x,
                    name_box_y,
                    slot.box_width,
                    slot.name_box_height,
                    slot.name_label,
                    bold=True,
                )
            if self.show_theme_field:
                self._draw_box(
                    canvas,
                    box_x,
                    theme_box_y,
                    slot.box_width,
                    slot.theme_box_height,
                    slot.theme_label,
                    bold=False,
                )
            canvas.setFillColor(colors.black)
            canvas.setFont("Helvetica-Bold", 11)
            canvas.drawCentredString(center, 0.08 * inch, str(slot.position))
        canvas.restoreState()

    def _draw_box(
        self,
        canvas: Canvas,
        x: float,
        y: float,
        width: float,
        height: float,
        label: str,
        *,
        bold: bool,
    ) -> None:
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1.2)
        canvas.setFillColor(colors.white)
        canvas.rect(x, y, width, height, fill=1, stroke=1)
        if label:
            canvas.setFillColor(colors.black)
            canvas.setFont("Helvetica-Bold" if bold else "Helvetica", 10.5 if bold else 9.3)
            canvas.drawCentredString(x + width / 2, y + height / 2 - 3.5, label)
