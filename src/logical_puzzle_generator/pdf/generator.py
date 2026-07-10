from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from logical_puzzle_generator.localization import Language, TranslationCatalog, parse_language
from logical_puzzle_generator.model.puzzle import Puzzle

from .renderer import TextRenderer


class PdfGenerator:
    """
    Presentation-only PDF generator for printable puzzles and solutions.
    """

    def __init__(
        self,
        text_renderer: TextRenderer | None = None,
        language: Language | str = Language.ENGLISH,
    ) -> None:
        self.language = parse_language(language)
        self._text_renderer = text_renderer if text_renderer is not None else TextRenderer(self.language)
        self._catalog = TranslationCatalog(self.language)
        self._styles = getSampleStyleSheet()
        self._styles.add(ParagraphStyle(name="ChildClue", parent=self._styles["BodyText"], fontSize=13, leading=17, spaceAfter=8))
        self._styles.add(ParagraphStyle(name="SectionHeading", parent=self._styles["Heading2"], fontSize=15, leading=18, spaceBefore=8, spaceAfter=8, textColor=colors.darkblue))

    def create(self, puzzle: Puzzle, filename: str | Path) -> None:
        """
        Backward-compatible wrapper for creating the unsolved puzzle PDF.
        """
        self.create_puzzle_pdf(puzzle, filename)

    def create_puzzle_pdf(self, puzzle: Puzzle, filename: str | Path) -> None:
        self._validate_puzzle(puzzle)
        output_path = self._prepare_output_path(filename)

        story: list[Any] = []
        story.extend(self._header(puzzle))
        story.append(Paragraph(self._catalog.label("clues"), self._styles["SectionHeading"]))
        for rendered_clue in self._text_renderer.render_clues(puzzle.clues, item_count=len(puzzle.items)):
            story.append(Paragraph(rendered_clue, self._styles["ChildClue"]))

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(self._catalog.label("solving_grid"), self._styles["SectionHeading"]))
        story.append(self._empty_grid(puzzle))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(self._catalog.label("players_items"), self._styles["SectionHeading"]))
        story.append(Paragraph(", ".join(item.name for item in puzzle.items), self._styles["BodyText"]))

        self._build(output_path, story)

    def create_solution_pdf(self, puzzle: Puzzle, filename: str | Path) -> None:
        self._validate_puzzle(puzzle)
        if puzzle.solution is None:
            raise ValueError("Cannot create a solution PDF because the puzzle has no Solution.")
        output_path = self._prepare_output_path(filename)

        story: list[Any] = []
        story.extend(self._header(puzzle))
        story.append(Paragraph(self._catalog.label("solution"), self._styles["Title"]))
        story.append(self._solution_table(puzzle))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(self._catalog.label("original_clues"), self._styles["SectionHeading"]))
        for rendered_clue in self._text_renderer.render_clues(puzzle.clues, item_count=len(puzzle.items)):
            story.append(Paragraph(rendered_clue, self._styles["ChildClue"]))

        self._build(output_path, story)

    def _header(self, puzzle: Puzzle) -> list[Any]:
        metadata = puzzle.metadata
        title = metadata.title if metadata is not None else self._catalog.label("logical_puzzle")
        theme = metadata.theme if metadata is not None else self._catalog.label("general")

        story: list[Any] = [Paragraph(self._catalog.title(title), self._styles["Title"])]
        story.append(Paragraph(f"{self._catalog.label('theme')}: {theme}", self._styles["BodyText"]))
        if metadata is not None and metadata.difficulty is not None:
            story.append(Paragraph(f"{self._catalog.label('difficulty')}: {metadata.difficulty}", self._styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))
        return story

    def _empty_grid(self, puzzle: Puzzle) -> Table:
        header = [self._catalog.label("position"), self._catalog.label("answer")]
        data = [header]
        for index in range(1, len(puzzle.items) + 1):
            data.append([str(index), ""])

        table = Table(
            data,
            colWidths=[1.2 * inch, 5.5 * inch],
            rowHeights=[0.4 * inch] + [0.78 * inch] * len(puzzle.items),
        )
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return table

    def _solution_table(self, puzzle: Puzzle) -> Table:
        data = [[self._catalog.label("position"), self._catalog.label("player_item")]]
        data.extend(self._text_renderer.render_solution_rows(puzzle))
        table = Table(data, colWidths=[1.2 * inch, 5.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return table

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
                pagesize=letter,
                pageCompression=0,
                leftMargin=0.7 * inch,
                rightMargin=0.7 * inch,
                topMargin=0.6 * inch,
                bottomMargin=0.6 * inch,
            )
            doc.build(story)
        except Exception as exc:
            raise OSError(f"Failed to write PDF to {output_path}: {exc}") from exc
