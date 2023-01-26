import pathlib
import typing
import wtforms
from starlette.requests import Request
from unittest import mock

from ohmyadmin.datasource.base import DataSource
from ohmyadmin.filters import BaseFilter, UnboundFilter
from ohmyadmin.testing import MarkupSelector
from tests.conftest import RequestFactory


class FilterForm(wtforms.Form):
    name = wtforms.StringField()


class MyFilter(BaseFilter):
    form_class = FilterForm
    indicator_template = 'indicator.html'

    def apply(self, request: Request, query: DataSource) -> DataSource:  # pragma: no cover
        return query

    def is_active(self, request: Request) -> bool:  # pragma: no cover
        return False


def test_creates_unbound_filter() -> None:
    unbound = MyFilter()
    assert isinstance(unbound, UnboundFilter)


async def test_fill_form(request_f: RequestFactory) -> None:
    unbound = MyFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-name=test')
    instance = await unbound.create(request)
    assert instance.form.name.data == 'test'


async def test_calls_initialize(request_f: RequestFactory) -> None:
    spy = mock.MagicMock()

    class MyFilter(BaseFilter):
        async def initialize(self, request: Request) -> None:
            spy()

        def apply(self, request: Request, query: DataSource) -> DataSource:  # pragma: no cover
            return query

        def is_active(self, request: Request) -> bool:  # pragma: no cover
            return False

    unbound = MyFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-name=test')
    await unbound.create(request)
    spy.assert_called_once()


async def test_returns_indicator_context(request_f: RequestFactory) -> None:
    unbound = MyFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-name=test')
    instance = await unbound.create(request)
    assert instance.get_indicator_context(value={'name': 'test'}) == {'name': 'test'}


async def test_renders_indicator_context(request_f: RequestFactory, extra_template_dir: pathlib.Path) -> None:
    (extra_template_dir / 'indicator.html').write_text('hello {{ indicator.name }}')

    class MyFilter(BaseFilter):
        indicator_template = 'indicator.html'

        def apply(self, request: Request, query: DataSource) -> DataSource:  # pragma: no cover
            return query

        def is_active(self, request: Request) -> bool:  # pragma: no cover
            return False

        def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
            return {'name': 'world'}

    unbound = MyFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-name=test')
    instance = await unbound.create(request)
    assert instance.render_indicator(request) == 'hello world'


async def test_exposes_variables_into_template(request_f: RequestFactory, extra_template_dir: pathlib.Path) -> None:
    (extra_template_dir / 'indicator.html').write_text(
        "'has_filter' if filter else ''\n"
        "'has_indicator' if indicator else ''\n"
        "'has_clear_url' if clear_url else ''\n"
    )

    class MyFilter(BaseFilter):
        indicator_template = 'indicator.html'

        def apply(self, request: Request, query: DataSource) -> DataSource:  # pragma: no cover
            return query

        def is_active(self, request: Request) -> bool:  # pragma: no cover
            return False

        def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
            return {'name': 'world'}

    unbound = MyFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-name=test')
    instance = await unbound.create(request)
    data = instance.render_indicator(request)
    assert 'has_filter' in data
    assert 'has_indicator' in data
    assert 'has_clear_url' in data


async def test_renders_form(request_f: RequestFactory, extra_template_dir: pathlib.Path) -> None:
    unbound = MyFilter('example')
    assert isinstance(unbound, UnboundFilter)

    request = request_f(query_string='example-name=test')
    instance = await unbound.create(request)
    page = MarkupSelector(instance.render_form(request))
    assert page.has_node('input[type="text"]')
    assert page.get_text('button.btn-accent') == 'Apply'
    assert page.get_text('button.btn-text') == 'Cancel'
