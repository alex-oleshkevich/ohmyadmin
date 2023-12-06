import datetime
from unittest import mock

from ohmyadmin.datasources.datasource import InMemoryDataSource
from ohmyadmin.filters import DateFilter, UnboundFilter
from ohmyadmin.testing import MarkupSelector
from tests.conftest import RequestFactory
from tests.models import Post


async def test_renders_form(request_f: RequestFactory) -> None:
    unbound = DateFilter("example")
    assert isinstance(unbound, UnboundFilter)

    request = request_f()
    instance = await unbound.create(request)
    content = instance.render_form(request)
    page = MarkupSelector(content)
    assert page.has_node('input[type="date"][name="example-query"]')


async def test_is_active(request_f: RequestFactory) -> None:
    unbound = DateFilter("example")
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string="example-query=2023-01-02")
    instance = await unbound.create(request)
    assert instance.is_active(request)

    request = request_f()
    instance = await unbound.create(request)
    assert not instance.is_active(request)


async def test_applies_filter(
    request_f: RequestFactory, datasource: InMemoryDataSource[Post]
) -> None:
    unbound = DateFilter("example")
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string="example-query=2023-01-02")
    instance = await unbound.create(request)
    with mock.patch.object(datasource, "apply_date_filter") as fn:
        instance.apply(request, datasource)
        fn.assert_called_once_with("example", datetime.date(2023, 1, 2))


async def test_not_applies_for_malformed_operation(
    request_f: RequestFactory,
    datasource: InMemoryDataSource[Post],
) -> None:
    unbound = DateFilter("example")
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string="example-query=2023")
    instance = await unbound.create(request)
    with mock.patch.object(datasource, "apply_date_filter") as fn:
        instance.apply(request, datasource)
        fn.assert_not_called()


async def test_renders_indicator(request_f: RequestFactory) -> None:
    unbound = DateFilter("example")
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string="example-query=2023-01-02")
    instance = await unbound.create(request)
    content = instance.render_indicator(request)
    page = MarkupSelector(content)
    assert page.get_text('[data-test="indicator"]') == "Example:\n\nJan 2, 2023"
