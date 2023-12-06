import datetime
import pytest
from starlette.requests import Request

from ohmyadmin.formatters import TimeFormatter
from ohmyadmin.testing import MarkupSelector


def test_time_formatter_with_datetime(http_request: Request) -> None:
    formatter = TimeFormatter(format="short")
    content = formatter.format(http_request, datetime.datetime(2023, 1, 2, 12, 30, 59))
    selector = MarkupSelector(content)
    assert selector.get_attribute("time", "datetime") == "2023-01-02T12:30:59"
    assert selector.get_attribute("time", "title") == "2023-01-02T12:30:59"


def test_time_formatter_with_time(http_request: Request) -> None:
    formatter = TimeFormatter(format="short")
    content = formatter.format(http_request, datetime.time(12, 30, 59))
    selector = MarkupSelector(content)
    assert selector.get_attribute("time", "datetime") == "12:30:59"
    assert selector.get_attribute("time", "title") == "12:30:59"


@pytest.mark.parametrize(
    "value", [datetime.datetime(2023, 1, 2, 12, 30, 59), datetime.time(12, 30, 59)]
)
def test_time_formatter_default_format(
    http_request: Request, value: datetime.time | datetime.datetime
) -> None:
    formatter = TimeFormatter()
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text("time") == "12:30 PM"


@pytest.mark.parametrize(
    "value", [datetime.datetime(2023, 1, 2, 12, 30, 59), datetime.time(12, 30, 59)]
)
def test_time_formatter_short_format(
    http_request: Request, value: datetime.time | datetime.datetime
) -> None:
    formatter = TimeFormatter(format="short")
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text("time") == "12:30 PM"


@pytest.mark.parametrize(
    "value", [datetime.datetime(2023, 1, 2, 12, 30, 59), datetime.time(12, 30, 59)]
)
def test_time_formatter_medium_format(
    http_request: Request, value: datetime.time | datetime.datetime
) -> None:
    formatter = TimeFormatter(format="medium")
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text("time") == "12:30:59 PM"


@pytest.mark.parametrize(
    "value", [datetime.datetime(2023, 1, 2, 12, 30, 59), datetime.time(12, 30, 59)]
)
def test_time_formatter_full_format(
    http_request: Request, value: datetime.time | datetime.datetime
) -> None:
    formatter = TimeFormatter(format="full")
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text("time") == "12:30:59 PM Coordinated Universal Time"
