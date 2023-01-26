import datetime
import pytest
from unittest import mock

from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.filters import DateRangeFilter, UnboundFilter
from ohmyadmin.testing import MarkupSelector
from tests.conftest import RequestFactory
from tests.models import Post


async def test_renders_form(request_f: RequestFactory) -> None:
    unbound = DateRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f()
    instance = await unbound.create(request)
    content = instance.render_form(request)
    page = MarkupSelector(content)
    assert page.has_node('input[type="date"][name="example-after"]')
    assert page.has_node('input[type="date"][name="example-before"]')


async def test_is_active(request_f: RequestFactory) -> None:
    unbound = DateRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-before=2023-01-02')
    instance = await unbound.create(request)
    assert instance.is_active(request)

    request = request_f(query_string='example-after=2023-01-02')
    instance = await unbound.create(request)
    assert instance.is_active(request)

    request = request_f(query_string='example-after=2023-01-02&example-before=2023-01-02')
    instance = await unbound.create(request)
    assert instance.is_active(request)

    request = request_f()
    instance = await unbound.create(request)
    assert not instance.is_active(request)


@pytest.mark.parametrize(
    'query_string, arguments',
    [
        ('example-before=2023-01-02', ('example', datetime.date(2023, 1, 2), None)),
        ('example-after=2023-01-02', ('example', None, datetime.date(2023, 1, 2))),
        (
            'example-after=2023-01-02&example-before=2023-01-02',
            ('example', datetime.date(2023, 1, 2), datetime.date(2023, 1, 2)),
        ),
    ],
)
async def test_applies_filter(
    request_f: RequestFactory, datasource: InMemoryDataSource[Post], query_string: str, arguments: tuple
) -> None:
    unbound = DateRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string=query_string)
    instance = await unbound.create(request)
    with mock.patch.object(datasource, 'apply_date_range_filter') as fn:
        instance.apply(request, datasource)
        fn.assert_called_once_with(*arguments)


async def test_not_applies_if_not_active(request_f: RequestFactory, datasource: InMemoryDataSource[Post]) -> None:
    unbound = DateRangeFilter('example')
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
    unbound = DateRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string=query_string)
    instance = await unbound.create(request)
    with mock.patch.object(datasource, 'apply_date_range_filter') as fn:
        instance.apply(request, datasource)
        fn.assert_not_called()


async def test_renders_indicator(request_f: RequestFactory) -> None:
    unbound = DateRangeFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-before=2023-01-02')
    instance = await unbound.create(request)
    content = instance.render_indicator(request)
    page = MarkupSelector(content)
    assert page.get_node_text('[data-test="indicator"]') == 'Example:\nbefore Jan 2, 2023'

    request = request_f(query_string='example-after=2023-01-02')
    instance = await unbound.create(request)
    content = instance.render_indicator(request)
    page = MarkupSelector(content)
    assert page.get_node_text('[data-test="indicator"]') == 'Example:\nafter Jan 2, 2023'

    request = request_f(query_string='example-after=2023-01-02&example-before=2023-01-02')
    instance = await unbound.create(request)
    content = instance.render_indicator(request)
    page = MarkupSelector(content)
    assert page.get_node_text('[data-test="indicator"]') == 'Example:\nbetween Jan 2, 2023\n and Jan 2, 2023'
