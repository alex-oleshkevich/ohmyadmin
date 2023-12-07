import abc
import dataclasses
import typing

import wtforms
from slugify import slugify
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.actions.actions import WithRoute
from ohmyadmin.forms.utils import create_form, validate_on_submit
from ohmyadmin.templating import render_to_response


@dataclasses.dataclass
class ObjectAction(abc.ABC):
    icon: str = ""
    label: str = "<unlabeled>"

    def get_label(self, request: Request, obj: typing.Any) -> str:
        return self.label

    def get_icon(self, request: Request, obj: typing.Any) -> str:
        return self.icon


@dataclasses.dataclass
class LinkAction(ObjectAction):
    target: typing.Literal["", "_blank"] = ""
    url: str | typing.Callable[[Request, typing.Any], str] = ""
    template = "ohmyadmin/actions/row_actions/link.html"

    def get_url(self, request: Request, obj: typing.Any) -> str:
        if callable(self.url):
            return self.url(request, obj)
        return self.url


ObjectCallbackHandler = typing.Callable[[Request, typing.Sequence[str]], typing.Awaitable[Response]]


@dataclasses.dataclass
class CallbackAction(ObjectAction, WithRoute):
    slug: str = ""
    dangerous: bool = False
    callback: ObjectCallbackHandler | None = None
    confirmation: str | typing.Callable[[Request, typing.Any], str] = ""
    request_method: typing.Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    template = "ohmyadmin/actions/row_actions/callback.html"

    async def dispatch(self, request: Request) -> Response:
        selected = request.query_params.getlist("selected")
        return await self.handle(request, selected)

    async def handle(self, request: Request, selected: typing.Sequence[str]) -> Response:
        if self.callback:
            return await self.callback(request, selected)
        raise NotImplementedError()

    def get_slug(self) -> str:
        return self.slug or slugify(self.label or str(id(self)))

    def get_confirmation(self, request: Request, obj: typing.Any) -> str:
        if callable(self.confirmation):
            return self.confirmation(request, obj)
        return self.confirmation

    def get_url_name(self, url_name_prefix: str) -> str:
        return url_name_prefix + ".row_action." + self.get_slug()


FormCallbackHandler = typing.Callable[[Request, typing.Sequence[str], wtforms.Form], typing.Awaitable[Response]]


@dataclasses.dataclass
class FormAction(ObjectAction, WithRoute):
    slug: str = ""
    dangerous: bool = False
    callback: FormCallbackHandler | None = None
    form_class: typing.Type[wtforms.Form] = wtforms.Form
    confirmation: str | typing.Callable[[Request, typing.Any], str] = ""
    template = "ohmyadmin/actions/row_actions/form.html"

    modal_title: str = ""
    modal_description: str = ""
    modal_template = "ohmyadmin/actions/row_actions/form_modal.html"

    async def dispatch(self, request: Request) -> Response:
        selected = request.query_params.getlist("selected")
        form = await self.create_form(request, selected)
        if await validate_on_submit(request, form):
            return await self.handle(request, selected, form)

        return render_to_response(request, self.modal_template, {"form": form, "action": self})

    async def handle(self, request: Request, selected: typing.Sequence[str], form: wtforms.Form) -> Response:
        if self.callback:
            return await self.callback(request, selected, form)
        raise NotImplementedError()

    async def create_form(self, request: Request, selected: typing.Sequence[str]) -> wtforms.Form:
        return await create_form(request, self.form_class)

    def get_slug(self) -> str:
        return self.slug or slugify(self.label or str(id(self)))

    def get_confirmation(self, request: Request, obj: typing.Any) -> str:
        if callable(self.confirmation):
            return self.confirmation(request, obj)
        return self.confirmation

    def get_url_name(self, url_name_prefix: str) -> str:
        return url_name_prefix + ".row_action." + self.get_slug()
