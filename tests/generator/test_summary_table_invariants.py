from __future__ import annotations

import pytest

from logical_puzzle_generator.generator.puzzle_book import SummaryRow, SummaryTable


def _row() -> SummaryRow:
    return SummaryRow("training", "training_1", ("a", "b", "c", "d"))


def test_summary_row_rejects_empty_ids_and_duplicate_values() -> None:
    with pytest.raises(ValueError, match="theme_category_id"):
        SummaryRow("", "training_1", ("a", "b", "c", "d"))
    with pytest.raises(ValueError, match="theme_category_instance_id"):
        SummaryRow("training", "", ("a", "b", "c", "d"))
    with pytest.raises(ValueError, match="non-empty strings"):
        SummaryRow("training", "training_1", ("a", "", "c", "d"))
    with pytest.raises(ValueError, match="distinct"):
        SummaryRow("training", "training_1", ("a", "a", "c", "d"))


def test_summary_table_accepts_zero_theme_rows() -> None:
    table = SummaryTable((1, 2, 3, 4), ("A", "B", "C", "D"), ())

    assert table.rows == ()


def test_summary_table_rejects_invalid_positions_and_row_lengths() -> None:
    with pytest.raises(ValueError, match="positive integers"):
        SummaryTable((True, 2, 3, 4), ("A", "B", "C", "D"), ())
    with pytest.raises(ValueError, match="ordered and contiguous"):
        SummaryTable((1, 3, 4, 5), ("A", "B", "C", "D"), ())
    with pytest.raises(ValueError, match="child names"):
        SummaryTable((1, 2, 3, 4), ("A", "", "C", "D"), ())
    with pytest.raises(ValueError, match="position count"):
        SummaryTable((1, 2, 3, 4), ("A", "B", "C", "D"), (SummaryRow("x", "x_1", ("a",)),))


def test_summary_table_accepts_position_sized_rows() -> None:
    table = SummaryTable((1, 2, 3, 4), ("A", "B", "C", "D"), (_row(),))

    assert table.rows == (_row(),)
