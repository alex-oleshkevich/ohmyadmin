import datetime
from starlette.requests import Request

from ohmyadmin.formatters import DateTimeFormatter
from ohmyadmin.testing import MarkupSelector


def test_datetime_formatter(http_request: Request) -> None:
    formatter = DateTimeFormatter(format="short")
    date = datetime.datetime(2023, 1, 2, 12, 30, 59)

    content = formatter.format(http_request, date)
    selector = MarkupSelector(content)
    assert selector.get_attribute("time", "datetime") == "2023-01-02T12:30:59"
    assert selector.get_attribute("time", "title") == "2023-01-02T12:30:59"


def test_datetime_formatter_short_format(http_request: Request) -> None:
    formatter = DateTimeFormatter(format="short")
    date = datetime.datetime(2023, 1, 2, 12, 30, 59)

    content = formatter.format(http_request, date)
    selector = MarkupSelector(content)
    assert selector.get_text("time") == "1/2/23, 12:30 PM"


def test_datetime_formatter_medium_format(http_request: Request) -> None:
    formatter = DateTimeFormatter(format="medium")
    date = datetime.datetime(2023, 1, 2, 12, 30, 59)

    content = formatter.format(http_request, date)
    selector = MarkupSelector(content)
    assert selector.get_text("time") == "Jan 2, 2023, 12:30:59 PM"


def test_datetime_formatter_full_format(http_request: Request) -> None:
    formatter = DateTimeFormatter(format="full")
    date = datetime.datetime(2023, 1, 2, 12, 30, 59)

    content = formatter.format(http_request, date)
    selector = MarkupSelector(content)
    assert (
        selector.get_text("time")
        == "Monday, January 2, 2023 at 12:30:59 PM Coordinated Universal Time"
    )
