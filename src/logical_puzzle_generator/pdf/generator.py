from __future__ import annotations

import random

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from logical_puzzle_generator.localization import Language, TranslationCatalog, parse_language
from logical_puzzle_generator.model.puzzle import Puzzle

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
        story.append(
            Paragraph(self._catalog.label("players_items"), self._styles["SectionHeading"])
        )
        story.append(
            Paragraph(", ".join(item.name for item in puzzle.items), self._styles["NameList"])
        )
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(self._catalog.label("clues"), self._styles["SectionHeading"]))
        for index, rendered_clue in enumerate(
            self._text_renderer.render_clues(puzzle.clues, item_count=len(puzzle.items)), start=1
        ):
            story.append(Paragraph(f"{index}.&nbsp;&nbsp;{rendered_clue}", self._styles["ChildClue"]))
        return story

    def _header(self, puzzle: Puzzle) -> list[Any]:
        metadata = puzzle.metadata
        title = metadata.title if metadata is not None else self._catalog.label("logical_puzzle")
        theme = metadata.theme if metadata is not None else self._catalog.label("general")

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

    def _lineup(self, puzzle: Puzzle, labels: list[str] | None = None) -> PlayerLineupRenderer:
        return PlayerLineupRenderer(
            item_count=len(puzzle.items),
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
