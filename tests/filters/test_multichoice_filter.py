from starlette.requests import Request
from unittest import mock

from ohmyadmin.datasources.datasource import InMemoryDataSource
from ohmyadmin.filters import MultiChoiceFilter, UnboundFilter
from ohmyadmin.testing import MarkupSelector
from tests.conftest import RequestFactory
from tests.models import Post


async def test_renders_form(request_f: RequestFactory) -> None:
    unbound = MultiChoiceFilter("example", choices=[])
    assert isinstance(unbound, UnboundFilter)

    request = request_f()
    instance = await unbound.create(request)
    content = instance.render_form(request)
    page = MarkupSelector(content)
    assert page.has_node('select[name="example-choice"][multiple]')


async def test_renders_form_with_async_choices(request_f: RequestFactory) -> None:
    async def async_choices(_: Request) -> list[tuple[str, str]]:
        return [("1", "One")]

    unbound = MultiChoiceFilter("example", choices=async_choices)
    assert isinstance(unbound, UnboundFilter)

    request = request_f()
    instance = await unbound.create(request)
    assert instance.form.choice.choices == [("1", "One")]


async def test_is_active(request_f: RequestFactory) -> None:
    unbound = MultiChoiceFilter("example", choices=[("1", "One")])
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string="example-choice=1")
    instance = await unbound.create(request)
    assert instance.is_active(request)

    request = request_f(query_string="example-choice=2")
    instance = await unbound.create(request)
    assert not instance.is_active(request)

    request = request_f()
    instance = await unbound.create(request)
    assert not instance.is_active(request)


async def test_applies_filter(
    request_f: RequestFactory, datasource: InMemoryDataSource[Post]
) -> None:
    unbound = MultiChoiceFilter("example", choices=[("1", "One")])
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string="example-choice=1")
    instance = await unbound.create(request)
    with mock.patch.object(datasource, "apply_choice_filter") as fn:
        instance.apply(request, datasource)
        fn.assert_called_once_with("example", ["1"], str)


async def test_applies_coercion(
    request_f: RequestFactory, datasource: InMemoryDataSource[Post]
) -> None:
    unbound = MultiChoiceFilter("example", choices=[(1, "One")], coerce=int)
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string="example-choice=1")
    instance = await unbound.create(request)
    with mock.patch.object(datasource, "apply_choice_filter") as fn:
        instance.apply(request, datasource)
        fn.assert_called_once_with("example", [1], int)


async def test_not_applies_for_malformed_operation(
    request_f: RequestFactory,
    datasource: InMemoryDataSource[Post],
) -> None:
    unbound = MultiChoiceFilter("example", choices=[("1", "One")])
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string="example-choice=2")
    instance = await unbound.create(request)
    with mock.patch.object(datasource, "apply_choice_filter") as fn:
        instance.apply(request, datasource)
        fn.assert_not_called()


async def test_renders_indicator(request_f: RequestFactory) -> None:
    unbound = MultiChoiceFilter("example", choices=[("1", "One"), ("2", "Two")])
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string="example-choice=1&example-choice=2")
    instance = await unbound.create(request)
    content = instance.render_indicator(request)
    page = MarkupSelector(content)
    assert page.get_text('[data-test="indicator"]') == "Example:\n\nis in One, Two"
