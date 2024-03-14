import abc
import typing

import slugify
from starlette.datastructures import URL
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route
from starlette.types import ASGIApp, Receive, Scope, Send

from ohmyadmin import metrics
from ohmyadmin.actions import actions
from ohmyadmin.breadcrumbs import Breadcrumb
from ohmyadmin.components.base import Component, PageToolbar


class Screen(abc.ABC):
    label: str = ""
    description: str = ""
    icon: str = ""
    group: str = ""
    show_in_menu: bool = True
    breadcrumbs: list[Breadcrumb] | None = None
    page_metrics: typing.Sequence[metrics.Metric] = tuple()
    page_toolbar: Component = PageToolbar()

    @property
    def slug(self) -> str:
        return slugify.slugify(str(self.label))

    @classmethod
    @property
    def url_name(cls) -> str:
        slug = slugify.slugify(".".join([cls.__module__, cls.__name__]))
        return f"ohmyadmin.screen.{slug}"

    def get_url(self, request: Request) -> URL:
        return request.url_for(self.url_name)

    def get_action_route_name(self, action: actions.Action) -> str:
        return f"{self.url_name}.actions.{action.slug}"

    def get_page_metrics(self) -> typing.Sequence[metrics.Metric]:
        return self.page_metrics

    def get_metrics_routes(self) -> typing.Sequence[BaseRoute]:
        return [metric.get_route(self.url_name) for metric in self.get_page_metrics()]

    def get_route(self) -> BaseRoute:
        return Mount(
            "",
            routes=[
                Route(path="/", endpoint=self.dispatch, name=self.url_name, methods=["get", "post"]),
                Mount("/metrics", routes=self.get_metrics_routes()),
            ],
            middleware=[
                Middleware(ExposeViewMiddleware, screen=self),
            ],
        )

    async def dispatch(self, request: Request) -> Response:
        raise NotImplementedError()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        response = await self.dispatch(request)
        await response(scope, receive, send)


class ExposeViewMiddleware:
    def __init__(self, app: ASGIApp, **variables: Screen) -> None:
        self.app = app
        self.variables = variables

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        for name, value in self.variables.items():
            setattr(request.state, name, value)

        await self.app(scope, receive, send)
