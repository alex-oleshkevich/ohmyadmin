import wtforms
from starlette.requests import Request

from ohmyadmin.forms import AsyncSelectField, Choices


async def async_choices(request: Request) -> Choices:
    return [('1', 'One')]


async def test_async_select_field_with_simple_choices() -> None:
    unbound_field = AsyncSelectField(choices=[('1', 'One')])
    field = unbound_field.bind(wtforms.Form(), '')
    assert field.choices == [('1', 'One')]


async def test_async_select_field_with_callback_choices() -> None:
    unbound_field = AsyncSelectField(choices=lambda: [('1', 'One')])
    field = unbound_field.bind(wtforms.Form(), '')
    assert field.choices == [('1', 'One')]


async def test_async_select_field_with_async_callback_choices(http_request: Request) -> None:
    unbound_field = AsyncSelectField(choices=async_choices)
    field = unbound_field.bind(wtforms.Form(), '')
    await field.init(http_request)
    assert field.choices == [('1', 'One')]
