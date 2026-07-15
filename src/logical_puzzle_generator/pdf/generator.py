from __future__ import annotations

import random
from collections import Counter, defaultdict

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from logical_puzzle_generator.localization import Language, TranslationCatalog, parse_language
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.puzzle import Puzzle
from logical_puzzle_generator.themes.presentation import ItemPresentationResolver
from logical_puzzle_generator.themes.registry import (
    DEFAULT_THEME_REGISTRY,
    ThemeCategoryDefinition,
    ThemeCategoryInstance,
    ThemeRegistry,
)

from .choice_box import ChoiceBoxRenderer
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
        theme_registry: ThemeRegistry = DEFAULT_THEME_REGISTRY,
    ) -> None:
        self.language = parse_language(language)
        self.puzzle_number = puzzle_number
        self._theme_registry = theme_registry
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
                name="Instruction",
                parent=self._styles["BodyText"],
                fontName="Helvetica-Bold",
                fontSize=12.5,
                leading=16,
                spaceAfter=8,
                textColor=colors.black,
            )
        )
        self._styles.add(
            ParagraphStyle(
                name="Footer",
                parent=self._styles["BodyText"],
                fontName="Helvetica",
                fontSize=9,
                leading=11,
                alignment=1,
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
        self._build(
            output_path, self._worksheet_story(puzzle, labels=self._solution_labels(puzzle))
        )

    def create_puzzle_book_pdf(self, puzzle_book, filename: str | Path) -> None:
        """Create the PuzzleBook puzzle PDF: position, theme pages, empty summary."""
        output_path = self._prepare_output_path(filename)
        story: list[Any] = []
        display_labels = self._book_display_labels(puzzle_book)
        total_pages = len(puzzle_book.theme_puzzles) + 2
        for index, puzzle in enumerate(puzzle_book.pages):
            self._validate_puzzle(puzzle)
            if index:
                story.append(PageBreak())
            story.extend(
                self._worksheet_story(
                    puzzle,
                    theme_title=puzzle_book.theme.localized_title(self.language),
                    question=(
                        self._catalog.label("position_question")
                        if index == 0
                        else display_labels[index - 1]
                    ),
                    instruction=(
                        self._catalog.label("position_instruction")
                        if index == 0
                        else self._catalog.label("theme_page_reminder")
                    ),
                    show_available_names=(index == 0),
                    show_theme_values=(index != 0),
                    show_child_field=True,
                    show_theme_field=(index != 0),
                    child_field_heading=self._catalog.label("name"),
                    theme_field_heading=("" if index == 0 else display_labels[index - 1]),
                )
            )
        story.append(PageBreak())
        story.extend(self._summary_table_story(puzzle_book, solved=False))
        self._build(output_path, story, page_count=total_pages)

    def create_puzzle_book_solution_pdf(self, puzzle_book, filename: str | Path) -> None:
        """Create the PuzzleBook solution PDF with only the completed summary table."""
        output_path = self._prepare_output_path(filename)
        self._build(output_path, self._summary_table_story(puzzle_book, solved=True), page_count=1)

    def _worksheet_story(
        self,
        puzzle: Puzzle,
        labels: list[str | tuple[str, str]] | None = None,
        *,
        theme_title: str | None = None,
        question: str | None = None,
        instruction: str | None = None,
        show_available_names: bool = True,
        show_theme_values: bool = True,
        show_child_field: bool | None = None,
        show_theme_field: bool | None = None,
        child_field_heading: str = "",
        theme_field_heading: str = "",
    ) -> list[Any]:
        story: list[Any] = []
        story.extend(self._header(puzzle, theme_title=theme_title, question=question))
        effective_instruction = instruction
        if effective_instruction is None:
            effective_instruction = self._standalone_instruction(puzzle)
        if effective_instruction:
            story.append(Spacer(1, 0.08 * inch))
            story.append(Paragraph(effective_instruction, self._styles["Instruction"]))
        story.append(Spacer(1, 0.10 * inch))
        story.append(
            self._lineup(
                puzzle,
                labels=labels,
                instruction="",
                show_child_field=show_child_field,
                show_theme_field=show_theme_field,
                child_field_heading=child_field_heading,
                theme_field_heading=theme_field_heading,
            )
        )
        story.append(Spacer(1, 0.18 * inch))
        story.append(Paragraph(self._catalog.label("clues"), self._styles["SectionHeading"]))
        resolver = self._resolver(puzzle)
        rendered_clues = self._text_renderer.render_clues(
            puzzle.clues, item_count=len(puzzle.items), presentation_resolver=resolver
        )
        for rendered_clue in rendered_clues:
            story.append(Paragraph(rendered_clue, self._styles["ChildClue"]))
        story.append(Spacer(1, 0.08 * inch))
        children = [
            resolver.item_label(item, short=True) if resolver is not None else item.name
            for item in puzzle.items
            if item.category_id == CHILDREN_CATEGORY_ID
        ]
        if show_available_names:
            story.append(self._choice_box(self._catalog.label("players_items"), children))
        if show_theme_values and self._is_themed(puzzle):
            story.append(Spacer(1, 0.08 * inch))
            story.append(
                self._choice_box(self._theme_category_label(puzzle), self._theme_values(puzzle))
            )
        return story

    def _summary_table_story(self, puzzle_book, *, solved: bool) -> list[Any]:
        summary = puzzle_book.summary_table
        story: list[Any] = [
            Paragraph(self._catalog.title("PuzzleBook Summary"), self._styles["WorksheetTitle"]),
            Spacer(1, 0.18 * inch),
        ]
        if solved:
            story.append(
                Paragraph(self._catalog.label("completed_summary"), self._styles["SectionHeading"])
            )
        else:
            story.append(
                Paragraph(self._catalog.label("summary_instruction"), self._styles["ChildClue"])
            )
        header = [self._catalog.label("question")] + [
            f"{self._catalog.label('position')} {position}" for position in summary.position_ids
        ]
        table_data: list[list[str]] = [header]
        table_data.append(
            [
                self._catalog.label("name"),
                *(
                    summary.child_names_by_position
                    if solved
                    else ["" for _ in summary.position_ids]
                ),
            ]
        )
        display_labels = self._book_display_labels(puzzle_book)
        for row_index, row in enumerate(summary.rows):
            category = puzzle_book.theme.category_by_id(row.theme_category_id)
            category_instance = self._category_instance_from_ids(
                category, row.theme_category_instance_id, row.value_ids_by_position
            )
            category_label = display_labels[row_index]
            values = (
                [
                    category_instance.value_by_id(value_id).display(self.language, short=True)
                    for value_id in row.value_ids_by_position
                ]
                if solved
                else ["" for _ in summary.position_ids]
            )
            table_data.append([category_label, *values])
        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(table)
        return story

    def _header(
        self, puzzle: Puzzle, *, theme_title: str | None = None, question: str | None = None
    ) -> list[Any]:
        metadata = puzzle.metadata
        title = question or self._theme_title(puzzle)
        theme = theme_title or (
            self._theme_title(puzzle)
            if self._is_themed(puzzle)
            else (metadata.theme if metadata is not None else self._catalog.label("general"))
        )

        story: list[Any] = [Paragraph(self._catalog.title(title), self._styles["WorksheetTitle"])]
        meta_parts: list[str] = []
        if self.puzzle_number is not None:
            meta_parts.append(f"{self._catalog.label('puzzle_number')}: {self.puzzle_number}")
        meta_parts.append(f"{self._catalog.label('theme')}: {theme}")
        if question is None and self._is_themed(puzzle):
            meta_parts.append(
                f"{self._catalog.label('question')}: {self._theme_category_label(puzzle)}"
            )
        elif question is not None:
            meta_parts.append(f"{self._catalog.label('question')}: {question}")
        if metadata is not None and metadata.difficulty is not None:
            difficulty_label = self._catalog.difficulty_label(metadata.difficulty)
            meta_parts.append(f"{self._catalog.label('difficulty')}: {difficulty_label}")
        story.append(Paragraph(" &nbsp; • &nbsp; ".join(meta_parts), self._styles["WorksheetMeta"]))
        return story

    def _choice_box(self, heading: str, values: list[str]):
        return ChoiceBoxRenderer(heading, values, self._styles["NameList"]).flowable()

    def _theme(self, puzzle: Puzzle):
        metadata = self._themed_metadata(puzzle)
        return self._theme_registry.resolve(metadata.theme_id)

    def _theme_title(self, puzzle: Puzzle) -> str:
        if not self._is_themed(puzzle):
            return (
                puzzle.metadata.title
                if puzzle.metadata is not None
                else self._catalog.label("general")
            )
        return self._theme(puzzle).localized_title(self.language)

    def _category_instance(self, puzzle: Puzzle) -> ThemeCategoryInstance:
        metadata = self._themed_metadata(puzzle)
        theme = self._theme(puzzle)
        category = theme.category_by_id(metadata.theme_category_id)
        return self._category_instance_from_ids(
            category, metadata.theme_category_instance_id, metadata.selected_theme_value_ids
        )

    def _category_instance_from_ids(
        self,
        category: ThemeCategoryDefinition,
        instance_id: str,
        selected_ids: tuple[str, ...],
    ) -> ThemeCategoryInstance:
        selected_values = tuple(
            (
                category.parse_generated_numeric_value_id(value_id, instance_id=instance_id)
                if category.is_numeric
                else category.value_by_id(value_id)
            )
            for value_id in selected_ids
        )
        if category.is_numeric:
            if len(selected_values) != 4:
                raise ValueError("Numeric category metadata must contain exactly four values.")
            if len({value.id for value in selected_values}) != 4:
                raise ValueError("Numeric category metadata contains duplicate value IDs.")
            numeric_values = [value.numeric_value for value in selected_values]
            if len(set(numeric_values)) != 4:
                raise ValueError("Numeric category metadata contains duplicate numeric values.")
        return ThemeCategoryInstance(category, instance_id, selected_values)

    def _is_themed(self, puzzle: Puzzle) -> bool:
        metadata = puzzle.metadata
        if metadata is None:
            return False
        fields = (
            metadata.theme_id,
            metadata.theme_category_id,
            metadata.theme_category_instance_id,
        )
        has_identity = any(value is not None for value in fields) or bool(
            metadata.selected_theme_value_ids
        )
        if not has_identity:
            return False
        self._validate_themed_metadata(puzzle)
        return True

    def _themed_metadata(self, puzzle: Puzzle):
        self._validate_themed_metadata(puzzle)
        if puzzle.metadata is None:
            raise ValueError("Themed puzzle metadata is required for themed PDF rendering.")
        assert puzzle.metadata.theme_id is not None
        assert puzzle.metadata.theme_category_id is not None
        assert puzzle.metadata.theme_category_instance_id is not None
        return puzzle.metadata

    def _validate_themed_metadata(self, puzzle: Puzzle) -> None:
        metadata = puzzle.metadata
        if metadata is None:
            raise ValueError("Themed puzzle metadata is required for themed PDF rendering.")
        missing = [
            name
            for name, value in (
                ("theme_id", metadata.theme_id),
                ("theme_category_id", metadata.theme_category_id),
                ("theme_category_instance_id", metadata.theme_category_instance_id),
            )
            if value is None
        ]
        if missing:
            raise ValueError(f"Incomplete themed puzzle metadata: missing {', '.join(missing)}.")
        if len(metadata.selected_theme_value_ids) != 4:
            raise ValueError(
                "Incomplete themed puzzle metadata: exactly four selected theme value IDs are required."
            )

    def _theme_category_label(self, puzzle: Puzzle) -> str:
        return self._category_instance(puzzle).definition.localized_label(self.language)

    def _theme_values(self, puzzle: Puzzle) -> list[str]:
        return [
            value.display(self.language, short=True)
            for value in self._category_instance(puzzle).selected_values
        ]

    def _resolver(self, puzzle: Puzzle) -> ItemPresentationResolver | None:
        if not self._is_themed(puzzle):
            return None
        return ItemPresentationResolver(
            self._theme(puzzle), self._category_instance(puzzle), self.language
        )

    def _standalone_instruction(self, puzzle: Puzzle) -> str:
        key = (
            "standalone_theme_instruction"
            if self._is_themed(puzzle)
            else "standalone_position_instruction"
        )
        return self._catalog.label(key)

    def _lineup(
        self,
        puzzle: Puzzle,
        labels: list[str | tuple[str, str]] | None = None,
        instruction: str | None = None,
        show_child_field: bool | None = None,
        show_theme_field: bool | None = None,
        child_field_heading: str = "",
        theme_field_heading: str = "",
    ) -> PlayerLineupRenderer:
        return PlayerLineupRenderer(
            item_count=len(
                [item for item in puzzle.items if item.category_id == CHILDREN_CATEGORY_ID]
            ),
            labels=labels,
            instruction=instruction or "",
            show_child_field=True if show_child_field is None else show_child_field,
            show_theme_field=(
                self._is_themed(puzzle) if show_theme_field is None else show_theme_field
            ),
            child_field_heading=child_field_heading,
            theme_field_heading=theme_field_heading,
        )

    def _solution_labels(self, puzzle: Puzzle):
        rows = self._text_renderer.render_solution_rows(puzzle, self._resolver(puzzle))
        if all(len(row) == 2 for row in rows):
            return [row[1] for row in rows]
        labels: list[tuple[str, str]] = []
        for row in rows:
            if len(row) != 3:
                raise ValueError("Themed solution rows must include a thematic value.")
            labels.append((row[1], row[2]))
        return labels

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

    def _book_display_labels(self, puzzle_book) -> list[str]:
        category_ids = [page.metadata.theme_category_id for page in puzzle_book.theme_puzzles]
        totals = Counter(category_ids)
        seen: defaultdict[str, int] = defaultdict(int)
        labels: list[str] = []
        for page in puzzle_book.theme_puzzles:
            metadata = page.metadata
            category_id = metadata.theme_category_id
            seen[category_id] += 1
            label = puzzle_book.theme.category_by_id(category_id).localized_label(self.language)
            if totals[category_id] > 1:
                label = f"{label} {seen[category_id]}"
            labels.append(label)
        return labels

    def _validate_page_count(self, page_count: int) -> None:
        if isinstance(page_count, bool) or not isinstance(page_count, int):
            raise ValueError("Page count must be a positive integer.")
        if page_count < 1:
            raise ValueError("Page count must be a positive integer.")

    def _page_footer(self, page_count: int):
        self._validate_page_count(page_count)

        def draw_footer(canvas, doc) -> None:
            canvas.saveState()
            canvas.setFont("Helvetica", 9)
            text = f"{self._catalog.label('page')} {doc.page} / {page_count}"
            canvas.drawCentredString(A4[0] / 2, 0.32 * inch, text)
            canvas.restoreState()

        return draw_footer

    def _build(self, output_path: Path, story: list[Any], *, page_count: int | None = None) -> None:
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
            if page_count is None:
                doc.build(story)
            else:
                self._validate_page_count(page_count)
                on_page = self._page_footer(page_count)
                doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
        except Exception as exc:
            raise OSError(f"Failed to write PDF to {output_path}: {exc}") from exc
