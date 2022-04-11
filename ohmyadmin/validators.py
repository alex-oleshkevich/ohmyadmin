import typing
import wtforms
from starlette.requests import Request

from ohmyadmin.forms import Form


class Validator(typing.Protocol):
    async def __call__(self, request: Request, form: Form, field: wtforms.Field) -> None:
        ...
