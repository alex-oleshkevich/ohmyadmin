import datetime
import pytest
from starlette.requests import Request

from ohmyadmin.formatters import DateFormatter
from ohmyadmin.testing import MarkupSelector


def test_date_formatter_with_datetime(http_request: Request) -> None:
    formatter = DateFormatter(format='short')

    content = formatter.format(http_request, datetime.datetime(2023, 1, 2, 12, 30, 59))
    selector = MarkupSelector(content)
    assert selector.get_attribute('time', 'datetime') == '2023-01-02T12:30:59'
    assert selector.get_attribute('time', 'title') == '2023-01-02T12:30:59'


def test_date_formatter_with_date(http_request: Request) -> None:
    formatter = DateFormatter(format='short')

    content = formatter.format(http_request, datetime.date(2023, 1, 2))
    selector = MarkupSelector(content)
    assert selector.get_attribute('time', 'datetime') == '2023-01-02'
    assert selector.get_attribute('time', 'title') == '2023-01-02'


@pytest.mark.parametrize('value', [datetime.datetime(2023, 1, 2, 12, 30, 59), datetime.date(2023, 1, 2)])
def test_date_formatter_short_format(http_request: Request, value: datetime.date | datetime.datetime) -> None:
    formatter = DateFormatter(format='short')
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text('time') == '1/2/23'


@pytest.mark.parametrize('value', [datetime.datetime(2023, 1, 2, 12, 30, 59), datetime.date(2023, 1, 2)])
def test_date_formatter_medium_format(http_request: Request, value: datetime.date | datetime.datetime) -> None:
    formatter = DateFormatter(format='medium')
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text('time') == 'Jan 2, 2023'


@pytest.mark.parametrize('value', [datetime.datetime(2023, 1, 2, 12, 30, 59), datetime.date(2023, 1, 2)])
def test_date_formatter_full_format(http_request: Request, value: datetime.date | datetime.datetime) -> None:
    formatter = DateFormatter(format='full')
    content = formatter.format(http_request, value)
    selector = MarkupSelector(content)
    assert selector.get_text('time') == 'Monday, January 2, 2023'
