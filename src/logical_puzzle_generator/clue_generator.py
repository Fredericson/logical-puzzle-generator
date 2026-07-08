from .constraints import FixedPosition, LeftOf, Adjacent
class ClueGenerator:
    def generate(self, assignment):
        clues=[]
        items=list(assignment.positions.keys())
        for i,p in assignment.positions.items():
            clues.append(FixedPosition(i,p))
        for i,a in enumerate(items):
            for b in items[i+1:]:
                if assignment.position_of(a)<assignment.position_of(b):
                    clues.append(LeftOf(a,b))
                if abs(assignment.position_of(a)-assignment.position_of(b))==1:
                    clues.append(Adjacent(a,b))
        return clues
