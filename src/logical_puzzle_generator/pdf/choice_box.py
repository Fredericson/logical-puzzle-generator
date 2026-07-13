from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle


class ChoiceBoxRenderer:
    """Reusable bordered two-by-two choice box for four display values."""

    def __init__(self, heading: str, values: list[str], style: ParagraphStyle) -> None:
        if len(values) != 4:
            raise ValueError("ChoiceBoxRenderer requires exactly four values.")
        self.heading = heading
        self.values = values
        self.style = style

    def flowable(self) -> Table:
        data = [
            [Paragraph(f"<b>{self.heading}</b>", self.style), ""],
            [Paragraph(self.values[0], self.style), Paragraph(self.values[1], self.style)],
            [Paragraph(self.values[2], self.style), Paragraph(self.values[3], self.style)],
        ]
        table = Table(data, colWidths=[3.2 * inch, 3.2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("SPAN", (0, 0), (1, 0)),
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("INNERGRID", (0, 1), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (1, 0), colors.whitesmoke),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return table
