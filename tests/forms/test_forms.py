import dataclasses

import wtforms
from starlette.requests import Request

from ohmyadmin.forms import (
    AsyncSelectField,
    Choices,
    create_form,
    init_form,
    iterate_form_fields,
    populate_object,
    safe_coerce,
    validate_form,
    validate_on_submit,
)
from tests.conftest import RequestFactory


async def async_choices(request: Request) -> Choices:
    return [('1', 'One')]


def sync_validator(form: wtforms.Form, field: wtforms.Field) -> None:
    if field.data == "fail":
        raise wtforms.ValidationError("Error.")


async def async_validator(form: wtforms.Form, field: wtforms.Field) -> None:
    if field.data == "fail":
        raise wtforms.ValidationError("Error.")


@dataclasses.dataclass
class Model:
    name: str
    options: str


class MyForm(wtforms.Form):
    name = wtforms.StringField()
    options = AsyncSelectField(choices=async_choices)


class SubForm(wtforms.Form):
    subname = wtforms.StringField()


class ComplexForm(wtforms.Form):
    name = wtforms.StringField()
    subname = wtforms.FormField(SubForm)
    subnames = wtforms.FieldList(wtforms.FormField(SubForm), min_entries=1)


async def test_create_form(request_f: RequestFactory) -> None:
    request = request_f(method='GET')
    form = await create_form(request, MyForm)
    assert form.name.data is None


async def test_create_form_prefills_from_model(request_f: RequestFactory) -> None:
    model = Model(name='modelname', options='modeloptions')
    request = request_f(method='GET')
    form = await create_form(request, MyForm, obj=model)
    assert form.name.data == 'modelname'


async def test_create_form_fill_async_fields(request_f: RequestFactory) -> None:
    request = request_f(method='GET')
    form = await create_form(request, MyForm)
    assert form.options.choices == [('1', 'One')]


async def test_iterate_form_fields() -> None:
    form = ComplexForm()
    fields = iter(iterate_form_fields(form))
    assert next(fields).name == 'name'
    assert next(fields).name == 'subname-subname'
    assert next(fields).name == 'subnames-0-subname'


async def test_init_form(http_request: Request) -> None:
    form = MyForm()
    await init_form(http_request, form)
    assert form.options.choices == [('1', 'One')]


async def test_sync_validation() -> None:
    class Form(wtforms.Form):
        name = wtforms.StringField(validators=[sync_validator])

    form = Form(data={"name": "valid"})
    assert await validate_form(form)

    form = Form(data={"name": "fail"})
    assert not await validate_form(form)
    assert form.name.errors == ["Error."]  # pragma: no cover - wtf?? py3.11 only


async def test_async_validation() -> None:
    class Form(wtforms.Form):
        name = wtforms.StringField(validators=[async_validator])

    form = Form(data={"name": "valid"})
    assert await validate_form(form)

    form = Form(data={"name": "fail"})
    assert not await validate_form(form)
    assert form.name.errors == ["Error."]


async def test_validate_on_submit(request_f: RequestFactory) -> None:
    class Form(wtforms.Form):
        name = wtforms.StringField(validators=[async_validator])

    form = Form(data={"name": "fail"})
    await validate_on_submit(request_f(method='GET'), form)
    assert not form.errors

    form = Form(data={"name": "fail"})
    await validate_on_submit(request_f(method='POST'), form)
    assert form.errors


async def test_populate_object(http_request: Request) -> None:
    form = MyForm(data={'name': 'NAME'})
    model = Model(name='', options='')
    await populate_object(http_request, form, model)
    assert model.name == 'NAME'


def test_safe_coerce() -> None:
    assert safe_coerce(int)(1) == 1
    assert safe_coerce(int)('1') == 1
    assert safe_coerce(int)('boom') is None
    assert safe_coerce(int)(None) is None
