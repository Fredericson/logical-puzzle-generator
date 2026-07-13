from __future__ import annotations

from dataclasses import dataclass

NUMERIC_VALUE_SEPARATOR = "_value_"


@dataclass(frozen=True, slots=True)
class ParsedNumericValueId:
    value_id: str
    instance_id: str
    numeric_value: int


def build_numeric_value_id(*, instance_id: str, numeric_value: int) -> str:
    if not isinstance(instance_id, str) or not instance_id:
        raise ValueError("Numeric value IDs require a non-empty category instance ID.")
    if not isinstance(numeric_value, int) or isinstance(numeric_value, bool):
        raise TypeError("Numeric value ID suffix must be an integer.")
    if numeric_value < 0:
        raise ValueError("Numeric value ID suffix must be non-negative.")
    return f"{instance_id}{NUMERIC_VALUE_SEPARATOR}{numeric_value}"


def parse_numeric_value_id(
    value_id: str,
    *,
    instance_id: str,
    minimum: int,
    maximum: int,
) -> ParsedNumericValueId:
    if not isinstance(value_id, str):
        raise TypeError("Numeric value ID must be a string.")
    if not value_id:
        raise ValueError("Numeric value ID must not be empty.")
    if not isinstance(instance_id, str) or not instance_id:
        raise ValueError("Numeric value ID parsing requires a non-empty category instance ID.")
    prefix = f"{instance_id}{NUMERIC_VALUE_SEPARATOR}"
    if not value_id.startswith(prefix):
        if NUMERIC_VALUE_SEPARATOR not in value_id:
            raise ValueError(
                f"Numeric value ID '{value_id}' is missing the '{NUMERIC_VALUE_SEPARATOR}' separator."
            )
        raise ValueError(
            f"Numeric value ID '{value_id}' does not belong to instance '{instance_id}'."
        )
    suffix = value_id.removeprefix(prefix)
    if suffix == "":
        raise ValueError(f"Numeric value ID '{value_id}' is missing its numeric suffix.")
    if not suffix.isdecimal():
        raise ValueError(f"Numeric value ID '{value_id}' has a non-decimal numeric suffix.")
    numeric_value = int(suffix)
    if not minimum <= numeric_value <= maximum:
        raise ValueError(
            f"Numeric value {numeric_value} is outside the configured range {minimum}-{maximum}."
        )
    return ParsedNumericValueId(
        value_id=value_id, instance_id=instance_id, numeric_value=numeric_value
    )
