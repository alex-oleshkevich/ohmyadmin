import typing
import wtforms


class Validator(typing.Protocol):
    async def __call__(self, form: wtforms.Form, field: wtforms.Field) -> None:
        ...
