import abc
import typing

from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route

from ohmyadmin.actions.actions import Action
from ohmyadmin.components import AutoDisplayLayout, DisplayLayoutBuilder
from ohmyadmin.datasources.datasource import NoObjectError
from ohmyadmin.templating import render_to_response
from ohmyadmin.screens.base import ExposeViewMiddleware, Screen
from ohmyadmin.display_fields import DisplayField


class DisplayScreen(Screen):
    fields: typing.Sequence[DisplayField] = tuple()
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
                "layout": layout_builder(request, instance),
            },
        )

    def get_route(self) -> BaseRoute:
        return Mount(
            "",
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
