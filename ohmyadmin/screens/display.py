import abc
import typing

from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route

from ohmyadmin import components
from ohmyadmin.actions.actions import Action
from ohmyadmin.datasources.datasource import NoObjectError
from ohmyadmin.templating import render_to_response
from ohmyadmin.screens.base import ExposeViewMiddleware, Screen
from ohmyadmin.screens.table import Column


class DisplayLayoutBuilder(typing.Protocol):
    def __call__(self, instance: typing.Any) -> components.Component:
        ...


class BaseDisplayLayoutBuilder(abc.ABC):
    def __call__(self, instance: typing.Any, fields: typing.Sequence[Column]) -> components.Component:
        return self.build(instance, fields)

    @abc.abstractmethod
    def build(self, instance: typing.Any, fields: typing.Sequence[Column]) -> components.Component:
        raise NotImplementedError()


class AutoDisplayLayout(BaseDisplayLayoutBuilder):
    def build(self, instance: typing.Any, fields: typing.Sequence[Column]) -> components.Component:
        return components.GridComponent(
            columns=12,
            children=[
                components.ColumnComponent(
                    colspan=6,
                    children=[
                        components.DisplayValueComponent(
                            label=field.label,
                            value=field.get_value(instance),
                            formatter=field.formatter,
                        )
                        for field in fields
                    ],
                )
            ],
        )


class DisplayScreen(Screen):
    fields: typing.Sequence[Column] = tuple()
    object_actions: typing.Sequence[Action] = tuple()
    layout_class: typing.Type[DisplayLayoutBuilder] = AutoDisplayLayout
    template = "ohmyadmin/screens/display/page.html"

    @abc.abstractmethod
    async def get_object(self, request: Request) -> typing.Any:
        raise NotImplementedError()

    def get_actions(self) -> typing.Sequence[Action]:
        return [action for action in self.object_actions]

    async def dispatch(self, request: Request) -> Response:
        try:
            instance = await self.get_object(request)
        except NoObjectError:
            raise HTTPException(404, "Page not found")

        layout_builder = self.layout_class()
        return render_to_response(
            request,
            self.template,
            {
                "screen": self,
                "model": instance,
                "page_title": self.label,
                "page_description": self.description,
                "layout": layout_builder(instance, self.fields),
            },
        )

    def get_route(self) -> BaseRoute:
        return Mount(
            "/" + self.slug,
            routes=[
                Route("/", self.dispatch, name=self.url_name),
                Mount(
                    "/actions",
                    routes=[
                        Route(
                            "/" + action.slug, action, name=self.get_action_route_name(action), methods=["get", "post"]
                        )
                        for action in self.object_actions
                    ],
                    middleware=[
                        Middleware(ExposeViewMiddleware, screen=self),
                    ],
                ),
            ],
        )

    def get_action_route_name(self, action: Action) -> str:
        return f"{self.url_name}.actions.{action.slug}"
