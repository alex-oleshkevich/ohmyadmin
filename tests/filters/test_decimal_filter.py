from unittest import mock

from ohmyadmin.datasource.base import NumberOperation
from ohmyadmin.datasource.memory import InMemoryDataSource
from ohmyadmin.filters import DecimalFilter, UnboundFilter
from ohmyadmin.testing import MarkupSelector
from tests.conftest import RequestFactory
from tests.models import Post


async def test_renders_form(request_f: RequestFactory) -> None:
    unbound = DecimalFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f()
    instance = await unbound.create(request)
    content = instance.render_form(request)
    page = MarkupSelector(content)
    assert page.has_node('input[type="number"][name="example-query"]')
    assert page.has_node('select[name="example-operation"]')


async def test_is_active(request_f: RequestFactory) -> None:
    unbound = DecimalFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-query=1&example-operation=eq')
    instance = await unbound.create(request)
    assert instance.is_active(request)

    request = request_f()
    instance = await unbound.create(request)
    assert not instance.is_active(request)


async def test_applies_filter(request_f: RequestFactory, datasource: InMemoryDataSource[Post]) -> None:
    unbound = DecimalFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-query=1&example-operation=eq')
    instance = await unbound.create(request)
    with mock.patch.object(datasource, 'apply_number_filter') as fn:
        instance.apply(request, datasource)
        fn.assert_called_once_with('example', NumberOperation.eq, 1)


async def test_not_applies_for_malformed_operation(
    request_f: RequestFactory,
    datasource: InMemoryDataSource[Post],
) -> None:
    unbound = DecimalFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-query=1&example-operation=error')
    instance = await unbound.create(request)
    with mock.patch.object(datasource, 'apply_number_filter') as fn:
        instance.apply(request, datasource)
        fn.assert_not_called()


async def test_renders_indicator(request_f: RequestFactory) -> None:
    unbound = DecimalFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-query=1&example-operation=eq')
    instance = await unbound.create(request)
    content = instance.render_indicator(request)
    page = MarkupSelector(content)
    assert page.get_node_text('[data-test="indicator"]') == 'Example:\n\nequals 1'
