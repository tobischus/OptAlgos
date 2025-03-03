from abc import ABC, abstractmethod

class OptimizationProblem(ABC):
    @abstractmethod
    def evaluate_solution(self, solution):
        pass

    @abstractmethod
    def create_empty_solution(self):
        pass
