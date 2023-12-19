import abc
import typing

import wtforms
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route

from ohmyadmin.actions import actions
from ohmyadmin.actions.actions import WithRoute
from ohmyadmin.forms.layouts import LayoutBuilder, VerticalLayout
from ohmyadmin.forms.utils import create_form, validate_on_submit
from ohmyadmin.templating import render_to_response
from ohmyadmin.views.base import ExposeViewMiddleware, View


class FormView(View):
    form_class: typing.Type[wtforms.Form] = wtforms.Form
    form_layout_class: typing.Type[LayoutBuilder] = VerticalLayout
    form_actions: typing.Sequence[actions.Action] | None = None
    template = "ohmyadmin/views/form/page.html"

    async def init_form(self, request: Request, form: wtforms.Form) -> None:
        pass

    async def get_object(self, request: Request) -> typing.Any:
        return None

    def get_form_actions(self) -> typing.Sequence[actions.Action]:
        return self.form_actions or []

    @abc.abstractmethod
    async def handle(self, request: Request, form: wtforms.Form) -> Response:
        raise NotImplementedError()

    async def dispatch(self, request: Request) -> Response:
        instance = await self.get_object(request)
        form = await create_form(request, self.form_class, instance)
        await self.init_form(request, form)
        if await validate_on_submit(request, form):
            return await self.handle(request, form)

        form_layout = self.form_layout_class()
        return render_to_response(
            request,
            self.template,
            {
                "form": self,
                "instance": instance,
                "page_title": self.label,
                "page_description": self.description,
                "form_layout": form_layout(form),
                "form_actions": self.get_form_actions(),
            },
        )

    def get_route(self) -> BaseRoute:
        return Mount(
            "/" + self.slug,
            routes=[
                Route("/", self.dispatch, name=self.url_name, methods=["get", "post"]),
                Mount(
                    "/actions",
                    routes=[
                        action.get_route(self.url_name)
                        for action in self.get_form_actions()
                        if isinstance(action, WithRoute)
                    ],
                    middleware=[
                        Middleware(ExposeViewMiddleware, view=self),
                    ],
                ),
            ],
        )
