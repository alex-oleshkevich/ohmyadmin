import typing
import wtforms
from starlette.requests import Request


class Validator(typing.Protocol):
    async def __call__(self, request: Request, form: wtforms.Form, field: wtforms.Field) -> None:
        ...
