import abc
import typing

import wtforms
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.actions import actions
from ohmyadmin.components.form import FormView
from ohmyadmin.forms.utils import create_form, validate_on_submit
from ohmyadmin.templating import render_to_response
from ohmyadmin.screens.base import Screen


class FormScreen(Screen):
    form_class: typing.Type[wtforms.Form] = wtforms.Form
    layout_class: typing.Type[FormView] = FormView
    form_actions: typing.Sequence[actions.Action] = tuple()
    template = "ohmyadmin/screens/form/page.html"

    async def init_form(self, request: Request, form: wtforms.Form) -> None:
        pass

    async def get_object(self, request: Request) -> typing.Any:
        return None

    def get_form_actions(self) -> typing.Sequence[actions.Action]:
        return self.form_actions

    @abc.abstractmethod
    async def handle(self, request: Request, form: wtforms.Form, instance: typing.Any) -> Response:
        raise NotImplementedError()

    async def dispatch(self, request: Request) -> Response:
        instance = await self.get_object(request)
        form = await create_form(request, self.form_class, instance)
        await self.init_form(request, form)
        if await validate_on_submit(request, form):
            return await self.handle(request, form, instance)

        component = self.layout_class(form, instance)
        return render_to_response(
            request,
            self.template,
            {
                "screen": self,
                "model": instance,
                "component": component,
                "page_title": self.label,
                "page_description": self.description,
                "form_actions": self.get_form_actions(),
            },
        )

    def get_action_handlers(self) -> typing.Sequence[actions.Action]:
        return [*super().get_action_handlers(), *self.get_form_actions()]
