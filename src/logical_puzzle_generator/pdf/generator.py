from __future__ import annotations

import random

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from logical_puzzle_generator.localization import Language, TranslationCatalog, parse_language
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.themes.registry import DEFAULT_THEME_REGISTRY

from .lineup import PlayerLineupRenderer
from .renderer import TextRenderer


class PdfGenerator:
    """
    Presentation-only PDF generator for printable puzzles and solutions.
    """

    def __init__(
        self,
        text_renderer: TextRenderer | None = None,
        language: Language | str = Language.ENGLISH,
        random_source: random.Random | None = None,
        puzzle_number: int | None = None,
    ) -> None:
        self.language = parse_language(language)
        self.puzzle_number = puzzle_number
        self._text_renderer = (
            text_renderer
            if text_renderer is not None
            else TextRenderer(self.language, random_source=random_source)
        )
        self._catalog = TranslationCatalog(self.language)
        self._styles = getSampleStyleSheet()
        self._styles.add(
            ParagraphStyle(
                name="WorksheetTitle",
                parent=self._styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=22,
                leading=26,
                alignment=1,
                spaceAfter=8,
                textColor=colors.black,
            )
        )
        self._styles.add(
            ParagraphStyle(
                name="WorksheetMeta",
                parent=self._styles["BodyText"],
                fontName="Helvetica",
                fontSize=10.5,
                leading=14,
                alignment=1,
                spaceAfter=2,
                textColor=colors.black,
            )
        )
        self._styles.add(
            ParagraphStyle(
                name="ChildClue",
                parent=self._styles["BodyText"],
                fontName="Helvetica",
                fontSize=12.5,
                leading=18,
                leftIndent=24,
                firstLineIndent=-24,
                spaceAfter=7,
                textColor=colors.black,
            )
        )
        self._styles.add(
            ParagraphStyle(
                name="SectionHeading",
                parent=self._styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                spaceBefore=10,
                spaceAfter=8,
                textColor=colors.black,
            )
        )
        self._styles.add(
            ParagraphStyle(
                name="NameList",
                parent=self._styles["BodyText"],
                fontName="Helvetica",
                fontSize=11.5,
                leading=15,
                spaceAfter=0,
            )
        )

    def create(self, puzzle: Puzzle, filename: str | Path) -> None:
        """
        Backward-compatible wrapper for creating the unsolved puzzle PDF.
        """
        self.create_puzzle_pdf(puzzle, filename)

    def create_puzzle_pdf(self, puzzle: Puzzle, filename: str | Path) -> None:
        self._validate_puzzle(puzzle)
        output_path = self._prepare_output_path(filename)
        self._build(output_path, self._worksheet_story(puzzle))

    def create_solution_pdf(self, puzzle: Puzzle, filename: str | Path) -> None:
        self._validate_puzzle(puzzle)
        if puzzle.solution is None:
            raise ValueError("Cannot create a solution PDF because the puzzle has no Solution.")
        output_path = self._prepare_output_path(filename)
        self._build(output_path, self._worksheet_story(puzzle, labels=self._solution_labels(puzzle)))

    def _worksheet_story(self, puzzle: Puzzle, labels: list[str] | None = None) -> list[Any]:
        story: list[Any] = []
        story.extend(self._header(puzzle))
        story.append(Spacer(1, 0.16 * inch))
        story.append(self._lineup(puzzle, labels=labels))
        story.append(Spacer(1, 0.18 * inch))
        story.append(Paragraph(self._catalog.label("clues"), self._styles["SectionHeading"]))
        for rendered_clue in self._text_renderer.render_clues(
            puzzle.clues, item_count=len(puzzle.items)
        ):
            story.append(Paragraph(rendered_clue, self._styles["ChildClue"]))
        story.append(Spacer(1, 0.08 * inch))
        children = [item.name for item in puzzle.items if item.category_id == "children"]
        story.append(self._choice_box(self._catalog.label("players_items"), children))
        story.append(Spacer(1, 0.08 * inch))
        story.append(self._choice_box(self._theme_category_label(puzzle), self._theme_values(puzzle)))
        return story

    def _header(self, puzzle: Puzzle) -> list[Any]:
        metadata = puzzle.metadata
        title = self._theme_title(puzzle)
        theme = self._theme_title(puzzle) if metadata is not None else self._catalog.label("general")

        story: list[Any] = [Paragraph(self._catalog.title(title), self._styles["WorksheetTitle"])]
        meta_parts: list[str] = []
        if self.puzzle_number is not None:
            meta_parts.append(f"{self._catalog.label('puzzle_number')}: {self.puzzle_number}")
        meta_parts.append(f"{self._catalog.label('theme')}: {theme}")
        if metadata is not None and metadata.difficulty is not None:
            difficulty_label = self._catalog.difficulty_label(metadata.difficulty)
            meta_parts.append(f"{self._catalog.label('difficulty')}: {difficulty_label}")
        story.append(Paragraph(" &nbsp; • &nbsp; ".join(meta_parts), self._styles["WorksheetMeta"]))
        return story

    def _choice_box(self, heading: str, values: list[str]) -> Table:
        cells = [[Paragraph(f"<b>{heading}</b>", self._styles["NameList"])] + [Paragraph(value, self._styles["NameList"]) for value in values]]
        table = Table(cells, colWidths=[1.45 * inch] + [1.3 * inch] * 4)
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (0, 0), colors.whitesmoke),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    def _theme(self, puzzle: Puzzle):
        if puzzle.metadata is None:
            return DEFAULT_THEME_REGISTRY.resolve()
        return DEFAULT_THEME_REGISTRY.resolve(puzzle.metadata.theme_id)

    def _theme_title(self, puzzle: Puzzle) -> str:
        return self._theme(puzzle).localized_title(self.language)

    def _theme_category_label(self, puzzle: Puzzle) -> str:
        return self._theme(puzzle).localized_category_label(self.language)

    def _theme_values(self, puzzle: Puzzle) -> list[str]:
        return [value.display(self.language, short=True) for value in self._theme(puzzle).values]

    def _lineup(self, puzzle: Puzzle, labels: list[str] | None = None) -> PlayerLineupRenderer:
        return PlayerLineupRenderer(
            item_count=len([item for item in puzzle.items if item.category_id == "children"]),
            labels=labels,
            instruction=self._catalog.label("solving_grid"),
        )

    def _solution_labels(self, puzzle: Puzzle) -> list[str]:
        return [name for _, name in self._text_renderer.render_solution_rows(puzzle)]

    def _validate_puzzle(self, puzzle: Puzzle) -> None:
        if not isinstance(puzzle, Puzzle):
            raise TypeError("PdfGenerator requires a Puzzle instance.")
        if not puzzle.items:
            raise ValueError("Cannot create a PDF for a puzzle with no items.")
        if any(not item.name for item in puzzle.items):
            raise ValueError("Cannot create a PDF because every puzzle item needs a name.")
        if not puzzle.clues:
            raise ValueError("Cannot create a PDF for a puzzle with no clues.")

    def _prepare_output_path(self, filename: str | Path) -> Path:
        output_path = Path(filename)
        if output_path.name == "":
            raise ValueError("PDF output path must include a file name.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    def _build(self, output_path: Path, story: list[Any]) -> None:
        try:
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                pageCompression=0,
                leftMargin=0.8 * inch,
                rightMargin=0.8 * inch,
                topMargin=0.55 * inch,
                bottomMargin=0.55 * inch,
            )
            doc.build(story)
        except Exception as exc:
            raise OSError(f"Failed to write PDF to {output_path}: {exc}") from exc
