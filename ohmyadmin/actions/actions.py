import abc
import dataclasses
import typing

import wtforms
from slugify import slugify
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route
from starlette.types import Receive, Scope, Send
from starlette_babel import gettext_lazy as _

from ohmyadmin.templating import render_to_response

ActionVariant = typing.Literal["accent", "default", "text", "danger"]


class Action:
    ...


@dataclasses.dataclass
class LinkAction(Action):
    url: str
    icon: str = ""
    target: typing.Literal["", "_blank"] = ""
    label: str = dataclasses.field(default_factory=lambda: _("Unlabeled"))
    template: str = "ohmyadmin/actions/link.html"


@dataclasses.dataclass
class EventAction(Action):
    event: str
    icon: str = ""
    trigger_from: str = "body"
    label: str = dataclasses.field(default_factory=lambda: _("Unlabeled"))
    data: typing.Any = None
    variant: ActionVariant = "default"
    template: str = "ohmyadmin/actions/event.html"


@dataclasses.dataclass
class CallFunctionAction(Action):
    function: str
    icon: str = ""
    label: str = dataclasses.field(default_factory=lambda: _("Unlabeled"))
    args: list[typing.Any] = dataclasses.field(default_factory=list)
    variant: ActionVariant = "default"
    template: str = "ohmyadmin/actions/call_function.html"


CallbackActionHandler = typing.Callable[[Request], typing.Awaitable[Response]]


class WithRoute(abc.ABC):
    @abc.abstractmethod
    def get_slug(self) -> str:
        raise NotImplementedError()

    def get_url_name(self, url_name_prefix: str) -> str:
        return url_name_prefix + ".action." + self.get_slug()

    def get_route(self, url_name_prefix: str) -> BaseRoute:
        return Route(
            "/" + self.get_slug(),
            self,
            name=self.get_url_name(url_name_prefix),
            methods=["get", "post", "put", "patch", "delete"],
        )


class Dispatchable(abc.ABC):
    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:
        raise NotImplementedError()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        response = await self.dispatch(request)
        await response(scope, receive, send)


@dataclasses.dataclass
class CallbackAction(Action, WithRoute, Dispatchable):
    callback: CallbackActionHandler
    icon: str = ""
    request_method: typing.Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    label: str = dataclasses.field(default_factory=lambda: _("Unlabeled"))
    variant: ActionVariant = "default"
    slug: str = ""
    template: str = "ohmyadmin/actions/callback.html"

    async def dispatch(self, request: Request) -> Response:
        return await self.callback(request)

    def get_slug(self) -> str:
        return self.slug or slugify(self.label or str(id(self)))


F = typing.TypeVar("F", bound=wtforms.Form)
FormActionHandler = typing.Callable[[Request, F], typing.Awaitable[Response]]


@dataclasses.dataclass
class FormAction(Action, WithRoute, Dispatchable):
    callback: FormActionHandler
    form_class: typing.Type[wtforms.Form]
    icon: str = ""
    slug: str = ""
    variant: ActionVariant = "default"
    template: str = "ohmyadmin/actions/form.html"
    modal_title: str = ""
    label: str = dataclasses.field(default_factory=lambda: _("Unlabeled"))

    modal_description: str = ""
    modal_template: str = "ohmyadmin/actions/form_modal.html"

    def get_slug(self) -> str:
        return self.slug or slugify(self.label or str(id(self)))

    async def create_form(self, request: Request) -> wtforms.Form:
        form = self.form_class(
            formdata=await request.form() if request.method == "POST" else None
        )
        await self.initialize_form(request, form)
        return form

    async def initialize_form(self, request: Request, form: wtforms.Form) -> None:
        pass

    async def validate_form(self, request: Request, form: wtforms.Form) -> None:
        form.validate()

    async def dispatch(self, request: Request) -> Response:
        form = await self.create_form(request)
        if request.method == "POST":
            await self.validate_form(request, form)
            return await self.callback(request, form)

        return render_to_response(
            request, self.modal_template, {"form": form, "action": self}
        )
