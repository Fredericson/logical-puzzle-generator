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

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash((type(self), tuple(sorted(self.__dict__.items()))))
