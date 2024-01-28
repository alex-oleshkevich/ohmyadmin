import random
import typing

import wtforms
from starlette.datastructures import URL
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from ohmyadmin import components, htmx
from ohmyadmin.components import BaseFormLayoutBuilder, Component, FormLayoutBuilder
from ohmyadmin.forms.utils import create_form, validate_on_submit
from ohmyadmin.templating import render_to_response

ActionVariant = typing.Literal["accent", "default", "text", "danger", "link", "primary"]


def random_slug() -> str:
    return "action-{id}".format(id=random.randint(100_000, 999_999))


class Action:
    icon: str = ""
    label: str = ""
    slug: str = ""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        response = await self.dispatch(request)
        await response(scope, receive, send)

    async def dispatch(self, request: Request) -> Response:
        raise NotImplementedError()


class LinkAction(Action):
    button_template: str = "ohmyadmin/actions/link.html"
    dropdown_template: str = "ohmyadmin/actions/link_menu.html"

    def __init__(
        self,
        url: str | URL = "",
        target: typing.Literal["", "_blank"] = "",
        label: str = "",
        icon: str = "",
        variant: ActionVariant = "link",
    ) -> None:
        self.url = url if isinstance(url, URL) else URL(url)
        self.target = target
        self.icon = icon or self.icon
        self.label = label or self.label
        self.variant = variant

    def get_url(self, request: Request, model: typing.Any | None = None) -> URL:
        return self.url


class SubmitAction(Action):
    def __init__(self, label: str = "", icon: str = "", name: str = "", variant: ActionVariant = "default") -> None:
        self.name = name
        self.variant = variant
        self.icon = icon or self.icon
        self.label = label or self.label

    button_template: str = "ohmyadmin/actions/submit.html"


ActionCallback: typing.TypeAlias = typing.Callable[[Request], typing.Awaitable[Response]]


class CallbackAction(Action):
    confirmation: str = ""
    dangerous: bool = False
    button_template: str = "ohmyadmin/actions/callback.html"
    dropdown_template: str = "ohmyadmin/actions/callback_menu.html"

    def __init__(
        self,
        label: str = "",
        callback: ActionCallback | None = None,
        dangerous: bool | None = None,
        icon: str = "",
        confirmation: str = "",
        variant: ActionVariant = "default",
    ) -> None:
        self.slug = random_slug()
        self.variant = variant
        self.callback = callback
        self.icon = icon or self.icon
        self.label = label or self.label
        self.confirmation = confirmation or self.confirmation
        self.dangerous = self.dangerous if dangerous is None else dangerous

    async def dispatch(self, request: Request) -> Response:
        if request.method == "POST":
            return await self.handle(request)
        raise HTTPException(405, "Method not allowed")

    async def handle(self, request: Request) -> Response:
        if self.callback:
            return await self.callback(request)
        raise NotImplementedError()


ModalActionCallback: typing.TypeAlias = typing.Callable[[Request, wtforms.Form], typing.Awaitable[Response]]


class ModalFormLayout(BaseFormLayoutBuilder):
    def build(self, form: wtforms.Form | wtforms.Field) -> Component:
        return components.Column([components.FormInput(field) for field in form])


class ModalAction(Action):
    dangerous: bool = False
    variant: ActionVariant = "default"
    form_class: type[wtforms.Form] = wtforms.Form
    form_builder_class: type[FormLayoutBuilder] = ModalFormLayout
    modal_title: str = ""
    modal_description: str = ""
    button_template: str = "ohmyadmin/actions/modal.html"
    modal_template: str = "ohmyadmin/actions/modal_modal.html"
    dropdown_template: str = "ohmyadmin/actions/modal_menu.html"

    def __init__(
        self,
        label: str = "",
        callback: ModalActionCallback | None = None,
        form_class: type[wtforms.Form] | None = None,
        dangerous: bool | None = None,
        icon: str = "",
        variant: ActionVariant = "default",
        form_builder_class: type[FormLayoutBuilder] | None = None,
        modal_title: str = "",
        modal_description: str = "",
    ) -> None:
        self.slug = random_slug()
        self.callback = callback
        self.modal_title = modal_title
        self.modal_description = modal_description
        self.icon = icon or self.icon
        self.label = label or self.label
        self.form_class = form_class or self.form_class
        self.dangerous = self.dangerous if dangerous is None else dangerous
        self.variant = "danger" if self.dangerous else variant
        self.form_builder_class = form_builder_class or self.form_builder_class

    async def initialize_form(self, request: Request, form: wtforms.Form) -> None:
        pass

    async def get_form_object(self, request: Request) -> typing.Any:
        return None

    def all_selected(self, request: Request) -> bool:
        return "__all__" in request.query_params

    def get_object_ids(self, request: Request) -> typing.Sequence[str]:
        return request.query_params.getlist("object_id")

    async def dispatch(self, request: Request) -> Response:
        instance = await self.get_form_object(request)
        form = await create_form(request, self.form_class, instance)
        await self.initialize_form(request, form)
        if await validate_on_submit(request, form):
            response = await self.handle(request, form)
            return htmx.close_modal(response)

        form_builder = self.form_builder_class()
        return render_to_response(
            request,
            self.modal_template,
            {
                "action": self,
                "object": instance,
                "form": form,
                "form_layout": form_builder(form),
            },
        )

    async def handle(self, request: Request, form: wtforms.Form) -> Response:
        if self.callback:
            return await self.callback(request, form)
        raise NotImplementedError()
