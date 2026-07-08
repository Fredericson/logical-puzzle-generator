class TextRenderer:
    def render(self, clues):
        lines=[]
        for i,c in enumerate(clues,1):
            lines.append(f"{i}. {c.__class__.__name__}")
        return lines
