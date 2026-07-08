from dataclasses import dataclass
from .assignment import Assignment

@dataclass(frozen=True)
class Solution:
    assignment: Assignment
