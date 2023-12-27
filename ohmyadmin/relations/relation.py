import typing

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from ohmyadmin.actions.actions import Action, ModalAction
from ohmyadmin.datasources.datasource import DataSource
from ohmyadmin.filters import Filter


class Relation:
    label: str = ""
    description: str = ""

    page_param: typing.ClassVar[str] = "page"
    page_size_param: typing.ClassVar[str] = "page_size"
    page_size: typing.ClassVar[int] = 25
    page_sizes: typing.ClassVar[typing.Sequence[int]] = [10, 25, 50, 100]
    ordering_param: typing.ClassVar[str] = "ordering"
    datasource: typing.ClassVar[DataSource | None] = None
    filters: typing.Sequence[Filter] = tuple()
    actions: typing.Sequence[Action] = tuple()
    row_actions: typing.Sequence[Action] = tuple()
    batch_actions: typing.Sequence[ModalAction] = tuple()
    search_param: str = "search"
    search_placeholder: str = ""
    template = "ohmyadmin/relations/relation.html"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        response = await self.dispatch(request)
        await response(scope, receive, send)

    async def dispatch(self, request: Request) -> Response:
        raise NotImplementedError()
