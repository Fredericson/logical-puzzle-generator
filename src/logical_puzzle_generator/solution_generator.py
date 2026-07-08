import random
from .assignment import Assignment
class SolutionGenerator:
    def generate(self, items):
        pos=list(range(1,len(items)+1))
        random.shuffle(pos)
        return Assignment(dict(zip(items,pos)))
