import decimal
import pytest
from starlette.requests import Request

from ohmyadmin.formatters import NumberFormatter, TextAlign
from ohmyadmin.testing import MarkupSelector


@pytest.mark.parametrize(
    "value, expected",
    [(42, "42"), (3.14, "3.14"), (decimal.Decimal("2.52688"), "2.527")],
)
def test_renders_digit(
    http_request: Request, value: int | float | decimal.Decimal, expected: str
) -> None:
    formatter = NumberFormatter()
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text("div") == expected


@pytest.mark.parametrize(
    "value, expected",
    [(42, "BYN42"), (3.14, "BYN3.14"), (decimal.Decimal("2.52688"), "BYN2.527")],
)
def test_renders_prefix(
    http_request: Request, value: int | float | decimal.Decimal, expected: str
) -> None:
    formatter = NumberFormatter(prefix="BYN")
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text("div") == expected


@pytest.mark.parametrize(
    "value, expected",
    [(42, "42BYN"), (3.14, "3.14BYN"), (decimal.Decimal("2.52688"), "2.527BYN")],
)
def test_renders_suffix(
    http_request: Request, value: int | float | decimal.Decimal, expected: str
) -> None:
    formatter = NumberFormatter(suffix="BYN")
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text("div") == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (42, "USD42BYN"),
        (3.14, "USD3.14BYN"),
        (decimal.Decimal("2.52688"), "USD2.527BYN"),
    ],
)
def test_renders_prefix_and_suffix(
    http_request: Request, value: int | float | decimal.Decimal, expected: str
) -> None:
    formatter = NumberFormatter(suffix="BYN", prefix="USD")
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text("div") == expected


@pytest.mark.parametrize("align", ["left", "center", "right"])
def test_renders_cell_alignment(http_request: Request, align: TextAlign) -> None:
    formatter = NumberFormatter(align=align)
    content = formatter.format(http_request, 1)
    selector = MarkupSelector(content)
    assert selector.get_style("div", "text-align") == align
