from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from logical_puzzle_generator.constraints.base import Constraint
from logical_puzzle_generator.model.category_ids import CHILDREN_CATEGORY_ID
from logical_puzzle_generator.model.item import Item


def _validate_child(item: Item, *, label: str) -> None:
    if not isinstance(item, Item):
        raise TypeError(f"{label} must be an Item.")
    if item.category_id != CHILDREN_CATEGORY_ID:
        raise ValueError(f"{label} must belong to the children category.")


def _validate_non_negative_int(value: int, *, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an integer.")
    if value < 0:
        raise ValueError(f"{label} must be non-negative.")


def _validate_positive_int(value: int, *, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an integer.")
    if value < 1:
        raise ValueError(f"{label} must be positive.")


class NumericCategoryConstraint(Constraint):
    def __init__(self, *, category_id: str, values_by_id: Mapping[str, int]) -> None:
        if not isinstance(category_id, str) or not category_id:
            raise ValueError("Numeric constraints require a non-empty category ID.")
        if not values_by_id:
            raise ValueError("Numeric constraints require value mappings.")
        copied: dict[str, int] = {}
        for value_id, value in values_by_id.items():
            if not isinstance(value_id, str) or not value_id:
                raise ValueError("Numeric value IDs must be non-empty strings.")
            _validate_non_negative_int(value, label=f"Numeric value for '{value_id}'")
            copied[value_id] = value
        if len(set(copied.values())) != len(copied):
            raise ValueError("Numeric value mappings must contain distinct numeric values.")
        self.category_id = category_id
        self.values_by_id = MappingProxyType(copied)

    @property
    def numeric_values(self) -> tuple[int, ...]:
        return tuple(self.values_by_id.values())

    def _value_for_child(self, assignment, child: Item) -> int:
        _validate_child(child, label="Numeric constraint child")
        if not assignment.contains(child):
            raise ValueError(f"Assignment does not contain child '{child}'.")
        child_position = assignment.position_of(child)
        paired_items = [
            item
            for item in assignment.items()
            if item.category_id == self.category_id
            and assignment.position_of(item) == child_position
        ]
        if not paired_items:
            raise ValueError(
                f"No numeric value from category '{self.category_id}' is paired with {child}."
            )
        if len(paired_items) > 1:
            raise ValueError(
                f"More than one numeric value from category '{self.category_id}' is paired with {child}."
            )
        paired = paired_items[0]
        if paired.name not in self.values_by_id:
            raise ValueError(
                f"Paired numeric value ID '{paired.name}' is not in the constraint mapping."
            )
        return self.values_by_id[paired.name]


class ExactNumericValueConstraint(NumericCategoryConstraint):
    def __init__(
        self, child: Item, value: int, *, category_id: str, values_by_id: Mapping[str, int]
    ) -> None:
        _validate_child(child, label="Exact numeric child")
        _validate_non_negative_int(value, label="Exact numeric value")
        super().__init__(category_id=category_id, values_by_id=values_by_id)
        if value not in self.numeric_values:
            raise ValueError("Exact numeric value must occur in the numeric mapping.")
        self.child = child
        self.value = value

    def matches(self, assignment) -> bool:
        return self._value_for_child(assignment, self.child) == self.value

    @property
    def description(self) -> str:
        return f"{self.child} has numeric value {self.value}"


class NumericDifferenceConstraint(NumericCategoryConstraint):
    def __init__(
        self,
        greater_child: Item,
        lesser_child: Item,
        difference: int,
        *,
        category_id: str,
        values_by_id: Mapping[str, int],
    ) -> None:
        _validate_child(greater_child, label="Greater child")
        _validate_child(lesser_child, label="Lesser child")
        if greater_child == lesser_child:
            raise ValueError("Difference operands must be distinct children.")
        _validate_positive_int(difference, label="Numeric difference")
        super().__init__(category_id=category_id, values_by_id=values_by_id)
        if not any(a == b + difference for a in self.numeric_values for b in self.numeric_values):
            raise ValueError("Numeric difference is not possible within the numeric mapping.")
        self.greater_child = greater_child
        self.lesser_child = lesser_child
        self.difference = difference

    def matches(self, assignment) -> bool:
        return (
            self._value_for_child(assignment, self.greater_child)
            == self._value_for_child(assignment, self.lesser_child) + self.difference
        )

    @property
    def description(self) -> str:
        return f"{self.greater_child} has {self.difference} more than {self.lesser_child}"


class NumericMultipleConstraint(NumericCategoryConstraint):
    def __init__(
        self,
        multiple_child: Item,
        base_child: Item,
        factor: int,
        *,
        category_id: str,
        values_by_id: Mapping[str, int],
    ) -> None:
        _validate_child(multiple_child, label="Multiple child")
        _validate_child(base_child, label="Base child")
        if multiple_child == base_child:
            raise ValueError("Multiple operands must be distinct children.")
        if not isinstance(factor, int) or isinstance(factor, bool):
            raise TypeError("Numeric multiple factor must be an integer.")
        if factor != 2:
            raise ValueError("Only factor 2 is supported.")
        super().__init__(category_id=category_id, values_by_id=values_by_id)
        if not any(a == factor * b for a in self.numeric_values for b in self.numeric_values):
            raise ValueError("Numeric multiple is not possible within the numeric mapping.")
        self.multiple_child = multiple_child
        self.base_child = base_child
        self.factor = factor

    def matches(self, assignment) -> bool:
        return self._value_for_child(
            assignment, self.multiple_child
        ) == self.factor * self._value_for_child(assignment, self.base_child)

    @property
    def description(self) -> str:
        return f"{self.multiple_child} has twice as many as {self.base_child}"
