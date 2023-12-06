import pytest

from ohmyadmin.datasources.datasource import NumberOperation, StringOperation


@pytest.mark.parametrize(
    "op", ["startswith", "endswith", "exact", "contains", "pattern"]
)
def test_string_operations(op: str) -> None:
    assert StringOperation[op]


def test_string_operation_choices() -> None:
    assert [
        ("exact", "same as"),
        ("startswith", "starts with"),
        ("endswith", "ends with"),
        ("contains", "contains"),
        ("pattern", "matches"),
    ] == [(x[0], str(x[1])) for x in StringOperation.choices()]


@pytest.mark.parametrize("op", ["eq", "gt", "gte", "lt", "lte"])
def test_number_operations(op: str) -> None:
    assert NumberOperation[op]


def test_number_operation_choices() -> None:
    assert [
        ("eq", "equals"),
        ("gt", "is greater than"),
        ("gte", "is greater than or equal"),
        ("lt", "is less than"),
        ("lte", "is less than or equal"),
    ] == [(x[0], str(x[1])) for x in NumberOperation.choices()]
