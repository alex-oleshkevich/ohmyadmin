import datetime
import pytest
from unittest import mock

from ohmyadmin.datasources.datasource import InMemoryDataSource
from ohmyadmin.filters import DateTimeRangeFilter, UnboundFilter
from ohmyadmin.testing import MarkupSelector
from tests.conftest import RequestFactory
from tests.models import Post


async def test_renders_form(request_f: RequestFactory) -> None:
    unbound = DateTimeRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f()
    instance = await unbound.create(request)
    content = instance.render_form(request)
    page = MarkupSelector(content)
    assert page.has_node('input[type="datetime-local"][name="example-after"]')
    assert page.has_node('input[type="datetime-local"][name="example-before"]')


@pytest.mark.parametrize(
    'query_string, expectation',
    [
        ('example-before=2023-01-02 00:00:00', True),
        ('example-after=2023-01-02 00:00:00', True),
        ('example-after=2023-01-02 00:00:00&example-before=2023-01-02 00:00:00', True),
        ('', False),
    ],
)
async def test_is_active(request_f: RequestFactory, query_string: str, expectation: bool) -> None:
    unbound = DateTimeRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string=query_string)
    instance = await unbound.create(request)
    assert instance.is_active(request) is expectation


@pytest.mark.parametrize(
    'query_string, arguments',
    [
        ('example-before=2023-01-02 00:00:00', ('example', datetime.datetime(2023, 1, 2, 0, 0, 0), None)),
        ('example-after=2023-01-02 00:00:00', ('example', None, datetime.datetime(2023, 1, 2, 0, 0, 0))),
        (
            'example-after=2023-01-02 00:00:00&example-before=2023-01-02 00:00:00',
            ('example', datetime.datetime(2023, 1, 2, 0, 0, 0), datetime.datetime(2023, 1, 2, 0, 0, 0)),
        ),
    ],
)
async def test_applies_filter(
    request_f: RequestFactory, datasource: InMemoryDataSource[Post], query_string: str, arguments: tuple
) -> None:
    unbound = DateTimeRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string=query_string)
    instance = await unbound.create(request)
    with mock.patch.object(datasource, 'apply_date_range_filter') as fn:
        instance.apply(request, datasource)
        fn.assert_called_once_with(*arguments)


async def test_not_applies_if_not_active(request_f: RequestFactory, datasource: InMemoryDataSource[Post]) -> None:
    unbound = DateTimeRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='')
    instance = await unbound.create(request)
    with mock.patch.object(datasource, 'apply_date_range_filter') as fn:
        instance.apply(request, datasource)
        fn.assert_not_called()


@pytest.mark.parametrize(
    'query_string', ['example-before=2023', 'example-after=2023', 'example-after=2023&example-before=2023']
)
async def test_not_applies_for_malformed_operation(
    request_f: RequestFactory,
    datasource: InMemoryDataSource[Post],
    query_string: str,
) -> None:
    unbound = DateTimeRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string=query_string)
    instance = await unbound.create(request)
    with mock.patch.object(datasource, 'apply_date_range_filter') as fn:
        instance.apply(request, datasource)
        fn.assert_not_called()


async def test_renders_indicator(request_f: RequestFactory) -> None:
    unbound = DateTimeRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-before=2023-01-02 00:00:00')
    instance = await unbound.create(request)
    content = instance.render_indicator(request)
    page = MarkupSelector(content)
    assert page.get_text('[data-test="indicator"]') == 'Example:\nbefore Jan 2, 2023, 12:00:00 AM'

    request = request_f(query_string='example-after=2023-01-02 00:00:00')
    instance = await unbound.create(request)
    content = instance.render_indicator(request)
    page = MarkupSelector(content)
    assert page.get_text('[data-test="indicator"]') == 'Example:\nafter Jan 2, 2023, 12:00:00 AM'

    request = request_f(query_string='example-after=2023-01-02 00:00:00&example-before=2023-01-02 00:00:00')
    instance = await unbound.create(request)
    content = instance.render_indicator(request)
    page = MarkupSelector(content)
    assert (
        page.get_text('[data-test="indicator"]')
        == 'Example:\nbetween Jan 2, 2023, 12:00:00 AM\n and Jan 2, 2023, 12:00:00 AM'
    )
