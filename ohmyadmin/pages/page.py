import inspect
import typing
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route
from starlette.types import Receive, Scope, Send

from ohmyadmin.pages.base import BasePage


class Page(BasePage):
    """
    A simple page that renders a template with context.

    Much like Starlette's HTTPEndpoint class.
    """

    template: typing.ClassVar[str] = 'ohmyadmin/pages/blank.html'

    async def get(self, request: Request) -> Response:
        return self.render_to_response(request, self.template, {'page_title': self.page_title})

    async def handler(self, request: Request) -> Response:
        method = request.method.lower()
        if handler := getattr(self, method, None):
            return (
                await handler(request)
                if inspect.iscoroutinefunction(handler)
                else await run_in_threadpool(handler, request)
            )
        raise HTTPException(405, 'Method Not Allowed')

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        request.state.page = self
        response = await self.handler(request)
        await response(scope, receive, send)

    def as_route(self) -> BaseRoute:
        methods: list[str] = []
        for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            if hasattr(self, method.lower()):
                methods.append(method)

        return Route(f'/{self.slug}', self, methods=methods, name=self.get_path_name())

    @classmethod
    def get_path_name(cls) -> str:
        return f'ohmyadmin.pages.{cls.slug}'
