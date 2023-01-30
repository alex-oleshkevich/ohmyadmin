import sqlalchemy as sa
import typing
from starlette.requests import Request

from ohmyadmin.forms import AsyncChoicesLoader


def choices_from(
    model_class: typing.Any,
    value_column: str = 'id',
    label_column: str = 'name',
    query: sa.Select | None = None,
) -> AsyncChoicesLoader:
    query = query or sa.select(model_class)

    async def loader(request: Request) -> typing.Sequence[tuple[typing.Any, str]]:
        result = await request.state.dbsession.scalars(query)
        choices: list[tuple[typing.Any, str]] = []
        for row in result:
            choices.append((getattr(row, value_column), getattr(row, label_column)))
        return choices

    return loader
