import abc
import typing

from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route

from ohmyadmin import components
from ohmyadmin.actions.actions import Action
from ohmyadmin.templating import render_to_response
from ohmyadmin.views.base import ExposeViewMiddleware, View


class DisplayLayoutBuilder(typing.Protocol):
    def __call__(self, instance: typing.Any) -> components.Component:
        ...


class BaseDisplayLayoutBuilder(abc.ABC):
    def __call__(self, instance: typing.Any) -> components.Component:
        return self.build(instance)

    @abc.abstractmethod
    def build(self, instance: typing.Any) -> components.Component:
        raise NotImplementedError()


class DisplayView(View):
    object_actions: typing.Sequence[Action] = tuple()
    layout_class: typing.Type[DisplayLayoutBuilder]
    template = "ohmyadmin/views/display/page.html"

    @abc.abstractmethod
    async def get_object(self, request: Request) -> typing.Any:
        raise NotImplementedError()

    def get_actions(self) -> typing.Sequence[Action]:
        return [action for action in self.object_actions]

    async def dispatch(self, request: Request) -> Response:
        instance = await self.get_object(request)
        layout_builder = self.layout_class()
        return render_to_response(
            request,
            self.template,
            {
                "view": self,
                "object": instance,
                "page_title": self.label,
                "page_description": self.description,
                "layout": layout_builder(instance),
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
                        Middleware(ExposeViewMiddleware, view=self),
                    ],
                ),
            ],
        )

    def get_action_route_name(self, action: Action) -> str:
        return f"{self.url_name}.actions.{action.slug}"
