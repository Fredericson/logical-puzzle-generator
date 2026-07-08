from __future__ import annotations

from abc import ABC, abstractmethod

class Constraint(ABC):
    """Base class for all constraints."""

    @abstractmethod
    def matches(self, assignment) -> bool:
        raise NotImplementedError()

    @property
    def description(self) -> str:
        return self.__class__.__name__

    def __call__(self, assignment):
        return self.matches(assignment)
