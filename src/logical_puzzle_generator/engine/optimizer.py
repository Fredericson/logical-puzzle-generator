from itertools import combinations

class Optimizer:
    def optimize(self, solver, items, constraints):
        for size in range(1,len(constraints)+1):
            for subset in combinations(constraints,size):
                if solver.count(items,list(subset))==1:
                    return list(subset)
        return list(constraints)
