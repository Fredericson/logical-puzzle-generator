from itertools import combinations
class ClueOptimizer:
    def optimize(self, solver, items, clues):
        for size in range(1,len(clues)+1):
            for subset in combinations(clues,size):
                if solver.count(items,list(subset))==1:
                    return list(subset)
        return clues
