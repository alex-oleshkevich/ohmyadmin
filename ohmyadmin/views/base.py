import abc
import typing

import slugify
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route
from starlette.types import ASGIApp, Receive, Scope, Send

from ohmyadmin.datasources.datasource import DataSource
from ohmyadmin.menu import MenuItem


class View(abc.ABC):
    label: str = ""
    description: str = ""
    group: str = ""
    show_in_menu: bool = True

    @property
    def slug(self) -> str:
        return slugify.slugify(self.label)

    @property
    def url_name(self) -> str:
        view_name = self.slug.replace("/", "_")
        return f"ohmyadmin.view.{view_name}"

    def get_url(self, request: Request) -> URL:
        return request.url_for(self.url_name)

    def get_route(self) -> BaseRoute:
        return Route(path="/" + self.slug, endpoint=self.dispatch, name=self.url_name)

    async def get_menu_item(self, request: Request) -> MenuItem:
        """Generate a menu item."""
        return MenuItem(label=self.label, group=self.group, url=self.get_url(request))

    async def dispatch(self, request: Request) -> Response:
        raise NotImplementedError()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        response = await self.dispatch(request)
        await response(scope, receive, send)


class ExposeViewMiddleware:
    def __init__(self, app: ASGIApp, **views: View) -> None:
        self.app = app
        self.views = views

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        for name, view in self.views.items():
            setattr(request.state, name, view)

        await self.app(scope, receive, send)


@typing.runtime_checkable
class HasFilters(typing.Protocol):
    def apply_filters(self, request: Request, query: DataSource) -> typing.Awaitable[DataSource]:
        ...
