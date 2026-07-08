from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

class PdfGenerator:
    def create(self,puzzle,filename):
        doc=SimpleDocTemplate(filename)
        styles=getSampleStyleSheet()
        story=[Paragraph("Logical Puzzle",styles["Title"])]
        story.append(Paragraph(f"Difficulty: {puzzle.difficulty}",styles["BodyText"]))
        story.append(Paragraph("Clues:",styles["Heading2"]))
        for idx, clue in enumerate(puzzle.clues,1):
            story.append(Paragraph(f"{idx}. {clue.__class__.__name__}",styles["BodyText"]))
        doc.build(story)
