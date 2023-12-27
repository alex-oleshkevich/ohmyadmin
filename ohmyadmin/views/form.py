import abc
import typing

import wtforms
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route

from ohmyadmin.actions import actions
from ohmyadmin.components import AutoLayout, FormLayoutBuilder
from ohmyadmin.forms.utils import create_form, validate_on_submit
from ohmyadmin.templating import render_to_response
from ohmyadmin.views.base import ExposeViewMiddleware, View


class FormView(View):
    form_class: typing.Type[wtforms.Form] = wtforms.Form
    layout_class: typing.Type[FormLayoutBuilder] = AutoLayout
    form_actions: typing.Sequence[actions.Action] | None = None
    template = "ohmyadmin/views/form/page.html"

    async def init_form(self, request: Request, form: wtforms.Form) -> None:
        pass

    async def get_object(self, request: Request) -> typing.Any:
        return None

    def get_form_actions(self) -> typing.Sequence[actions.Action]:
        return self.form_actions or []

    @abc.abstractmethod
    async def handle(self, request: Request, form: wtforms.Form, instance: typing.Any) -> Response:
        raise NotImplementedError()

    async def dispatch(self, request: Request) -> Response:
        instance = await self.get_object(request)
        form = await create_form(request, self.form_class, instance)
        await self.init_form(request, form)
        if await validate_on_submit(request, form):
            return await self.handle(request, form, instance)

        form_layout = self.layout_class()
        return render_to_response(
            request,
            self.template,
            {
                "form": self,
                "instance": instance,
                "form_layout": form_layout(form),
                "page_description": self.description,
                "form_actions": self.get_form_actions(),
                "page_title": self.label,
            },
        )

    def get_route(self) -> BaseRoute:
        return Mount(
            "/",
            routes=[
                Route("/", self.dispatch, name=self.url_name, methods=["get", "post"]),
                Mount(
                    "/actions",
                    routes=[
                        Route(
                            "/" + action.slug, action, name=self.get_action_route_name(action), methods=["get", "post"]
                        )
                        for action in self.get_form_actions()
                    ],
                    middleware=[
                        Middleware(ExposeViewMiddleware, view=self),
                    ],
                ),
            ],
        )

    def get_action_route_name(self, action: actions.Action) -> str:
        return f"{self.url_name}.actions.{action.slug}"
