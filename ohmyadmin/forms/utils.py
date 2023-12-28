import abc
import enum
import inspect
import typing
import wtforms
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import ImmutableMultiDict
from starlette.requests import Request

_F = typing.TypeVar("_F", bound=wtforms.Form)


class Initable(abc.ABC):  # pragma: no cover
    @abc.abstractmethod
    async def init(self, request: Request) -> None:
        ...


class Processable(abc.ABC):  # pragma: no cover
    @abc.abstractmethod
    async def process(self, request: Request) -> None:
        ...


async def create_form(
    request: Request,
    form_class: type[_F],
    obj: typing.Any | None = None,
    form_data: ImmutableMultiDict | None = None,
    prefix: str = "",
) -> _F:
    form_data = form_data or (None if request.method in ["GET", "HEAD", "OPTIONS"] else await request.form())
    form = form_class(form_data, obj=obj, prefix=prefix)
    await init_form(request, form)
    return form


def iterate_form_fields(
    form: typing.Iterable[wtforms.Field],
) -> typing.Generator[wtforms.Field, None, None]:
    for field in form:
        if isinstance(field, (wtforms.FieldList, wtforms.FormField)):
            yield from iterate_form_fields(field)
        else:
            yield field


async def init_form(request: Request, form: wtforms.Form) -> None:
    for field in iterate_form_fields(form):
        if isinstance(field, Initable):
            await field.init(request)


async def validate_form(form: wtforms.Form) -> bool:
    """
    Perform form validation.

    This function does not call Form.validate or Field.validate, instead it implements own logic that supports async
    validators.
    """
    is_valid = True
    for field in iterate_form_fields(form):
        for validator in field.validators:
            field.errors = list(field.errors) if field.errors is not None else []
            try:
                if inspect.iscoroutinefunction(validator):
                    await validator(form, field)
                else:
                    await run_in_threadpool(validator, form, field)
            except (wtforms.ValidationError, wtforms.validators.StopValidation) as ex:
                field.errors = list(field.errors)
                field.errors.extend(ex.args)
                is_valid = False
    return is_valid


async def validate_on_submit(request: Request, form: wtforms.Form) -> bool:
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        return await validate_form(form)
    return False


async def populate_object(request: Request, form: wtforms.Form, obj: typing.Any) -> None:
    form.populate_obj(obj)


def safe_enum_coerce(value: typing.Any, choices: type[enum.Enum]) -> typing.Any:
    try:
        return choices[value]
    except KeyError:
        return None


def safe_int_coerce(value: typing.Any) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
