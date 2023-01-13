import typing
import wtforms
from starlette.requests import Request

_F = typing.TypeVar('_F', bound=wtforms.Form)


async def create_form(request: Request, form_class: type[_F], obj: typing.Any | None = None) -> _F:
    form_data = None if request.method in ['GET', 'HEAD', 'OPTIONS'] else await request.form()
    return form_class(form_data, obj=obj)


async def validate_form(form: wtforms.Form) -> bool:
    return form.validate()


async def validate_on_submit(request: Request, form: wtforms.Form) -> bool:
    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        return await validate_form(form)
    return False
