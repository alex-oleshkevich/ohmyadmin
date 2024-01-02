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
from ohmyadmin.menu import MenuItem


class Screen(abc.ABC):
    label: str = ""
    description: str = ""
    icon: str = ""
    group: str = ""
    show_in_menu: bool = True
    breadcrumbs: list[Breadcrumb] | None = None
    page_actions: typing.Sequence[actions.Action] = tuple()
    page_metrics: typing.Sequence[metrics.Metric] = tuple()

    @property
    def slug(self) -> str:
        return slugify.slugify(self.label)

    @property
    def url_name(self) -> str:
        view_name = self.slug.replace("/", "_")
        return f"ohmyadmin.screen.{view_name}"

    def get_url(self, request: Request) -> URL:
        return request.url_for(self.url_name)

    def get_action_route_name(self, action: actions.Action) -> str:
        return f"{self.url_name}.actions.{action.slug}"

    def get_action_handlers(self) -> typing.Sequence[actions.Action]:
        return self.page_actions

    def get_page_metrics(self) -> typing.Sequence[metrics.Metric]:
        return self.page_metrics

    def get_action_routes(self) -> typing.Sequence[BaseRoute]:
        return [
            Route("/" + action.slug, action, name=self.get_action_route_name(action), methods=["get", "post"])
            for action in self.get_action_handlers()
        ]

    def get_metrics_routes(self) -> typing.Sequence[BaseRoute]:
        return [metric.get_route(self.url_name) for metric in self.get_page_metrics()]

    def get_route(self) -> BaseRoute:
        return Mount(
            "",
            routes=[
                Route(path="/", endpoint=self.dispatch, name=self.url_name, methods=["get", "post"]),
                Mount("/actions", routes=self.get_action_routes()),
                Mount("/metrics", routes=self.get_metrics_routes()),
            ],
            middleware=[
                Middleware(ExposeViewMiddleware, screen=self),
            ],
        )

    async def get_menu_item(self, request: Request) -> MenuItem:
        """Generate a menu item."""
        return MenuItem(label=self.label, group=self.group, url=self.get_url(request), icon=self.icon)

    def get_page_actions(self) -> typing.Sequence[actions.Action]:
        return self.page_actions

    def get_page_metrics(self) -> typing.Sequence[metrics.Metric]:
        return self.page_metrics

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
