import abc
import inspect
import typing
import wtforms
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

_F = typing.TypeVar('_F', bound=wtforms.Form)


async def create_form(request: Request, form_class: type[_F], obj: typing.Any | None = None) -> _F:
    form_data = None if request.method in ['GET', 'HEAD', 'OPTIONS'] else await request.form()
    return form_class(form_data, obj=obj)


def iterate_form_fields(form: typing.Iterable[wtforms.Field]) -> typing.Generator[wtforms.Field, None, None]:
    for field in form:
        if isinstance(field, (wtforms.FieldList, wtforms.FormField)):
            yield from iterate_form_fields(form)
        else:
            yield field


async def validate_form(form: wtforms.Form) -> bool:
    """
    Perform form validation.

    This function does not call Form.validate or Field.validate, instead it
    implements own logic that supports async validators.
    """
    is_valid = True
    for field in iterate_form_fields(form):
        for validator in field.validators:
            try:
                if inspect.iscoroutinefunction(validator):
                    await validator(form, field)
                else:
                    await run_in_threadpool(validator, form, field)
            except wtforms.ValidationError as ex:
                field.errors = list(field.errors)
                field.errors.extend(ex.args)
                is_valid = False
    return is_valid


async def validate_on_submit(request: Request, form: wtforms.Form) -> bool:
    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        return await validate_form(form)
    return False


async def populate_object(request: Request, form: wtforms.Form, obj: typing.Any) -> None:
    form.populate_obj(obj)


class Preparable(abc.ABC):
    @abc.abstractmethod
    async def prepare(self, request: Request) -> None:
        ...


class Processable(abc.ABC):
    @abc.abstractmethod
    async def process(self, request: Request) -> None:
        ...


class AsyncSelectField(wtforms.SelectField):
    ...
