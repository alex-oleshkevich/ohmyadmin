import inspect
import typing
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route

from ohmyadmin.pages.base import BasePage
from ohmyadmin.pages.pagemixins import Dispatchable


class TemplatePage(Dispatchable, BasePage):
    """
    A simple page that renders a template with context.

    Much like Starlette's HTTPEndpoint class.
    """

    template: typing.ClassVar[str] = 'ohmyadmin/pages/blank.html'

    async def handle(self, request: Request) -> typing.Mapping[str, typing.Any]:
        """Execute business logic here and return template context."""
        return {}

    async def get(self, request: Request) -> Response:
        context = dict(await self.handle(request))
        context.update({'page_title': self.page_title})
        return self.render_to_response(request, self.template, context)

    async def dispatch(self, request: Request) -> Response:
        method = request.method.lower()
        if handler := getattr(self, method, None):
            return (
                await handler(request)
                if inspect.iscoroutinefunction(handler)
                else await run_in_threadpool(handler, request)
            )
        raise HTTPException(405, 'Method Not Allowed')

    def as_route(self) -> BaseRoute:
        """
        Create route for this page.

        It will automatically detect used HTTP methods using defined methods.
        For example, if page has `def get` and `def post` methods then route
        will serve GET, HEAD, and POST verbs.
        """
        methods: list[str] = []
        for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            if hasattr(self, method.lower()):
                methods.append(method)

        return Route(f'/{self.slug}', self, methods=methods, name=self.get_path_name())
