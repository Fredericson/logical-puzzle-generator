class DifficultyCalculator:
    def calculate(self,n:int)->int:
        return min(5,max(1,(n+1)//2))
