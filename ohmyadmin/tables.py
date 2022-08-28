import dataclasses

import abc
import typing
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.actions import Action


@dataclasses.dataclass
class Column:
    name: str
    label: str
    sortable: bool
    searchable: bool


@dataclasses.dataclass
class BatchAction(abc.ABC):
    id: str
    label: str
    confirmation: str = ''
    dangerous: bool = False

    async def apply(self, request: Request, ids: list[str], params: dict[str, str]) -> Response:
        return Response()


@dataclasses.dataclass
class TableView:
    id: str
    columns: list[Column]
    actions: list[Action] = dataclasses.field(default_factory=list)
    row_actions: list[Action] = dataclasses.field(default_factory=list)
    batch_actions: list[BatchAction] = dataclasses.field(default_factory=list)
    page: int = 1
    page_param: str = 'page'
    page_size: int = 50
    page_size_param: str = 'page_size'

    async def render(self, request: Request) -> str:
        pass

    @classmethod
    def as_view(cls) -> typing.Callable[[Request], typing.Awaitable[Response]]:
        async def view(request: Request) -> Response:
            table = cls()
            content = await table.render(request)
            return Response(content)

        return view
