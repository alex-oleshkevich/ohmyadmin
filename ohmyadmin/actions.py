from __future__ import annotations

import dataclasses

import abc
import enum
import typing
from slugify import slugify
from starlette.requests import Request
from starlette.types import Receive, Scope, Send

from ohmyadmin.components import ButtonColor, Component, FormElement, Grid
from ohmyadmin.flash import FlashCategory
from ohmyadmin.forms import Form
from ohmyadmin.globals import get_current_request
from ohmyadmin.helpers import camel_to_sentence, render_to_response
from ohmyadmin.i18n import _
from ohmyadmin.responses import Response

if typing.TYPE_CHECKING:
    from ohmyadmin.resources import Resource, ResourceAction

_action_registry: dict[str, typing.Type[Action]] = {}

DISMISS_EVENT = 'modals.dismiss'


def get_action_by_id(action_id: str) -> typing.Type[Action]:
    return _action_registry[action_id]


class ActionMeta(abc.ABCMeta):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        name = name.removesuffix('Action')
        qual_name = '{module}-{klass}'.format(
            module=attrs['__module__'], klass=camel_to_sentence(attrs['__qualname__'])
        )

        attrs['id'] = attrs.get('id', slugify(qual_name))
        attrs['label'] = attrs.get('label', camel_to_sentence(name))

        klass = super().__new__(cls, name, bases, attrs)
        _action_registry[attrs['id']] = typing.cast(typing.Type['Action'], klass)
        return klass


class BaseAction(Component, abc.ABC, metaclass=ActionMeta):
    id: typing.ClassVar[str] = ''
    label: typing.ClassVar[str] = ''
    title: typing.ClassVar[str] = _('Do you want to run this action?')
    message: typing.ClassVar[str] = ''
    icon: typing.ClassVar[str] = ''
    dangerous: typing.ClassVar[bool] = False
    color: typing.ClassVar[ButtonColor] = 'default'
    template: str = 'ohmyadmin/components/action.html'

    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:
        ...

    @property
    def url(self) -> str:
        request = get_current_request()
        return request.url_for('ohmyadmin_action', action_id=self.id)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = await self.dispatch(Request(scope, receive, send))
        await response(scope, receive, send)


class Action(BaseAction):
    success_message: str = _('Action has been completed.')
    form_class: typing.ClassVar[typing.Type[Form]] = Form

    def get_form_class(self) -> typing.Type[Form]:
        return getattr(self, 'ActionForm', self.form_class)

    def get_form_layout(self, form: Form) -> Component:
        return Grid(columns=1, children=[FormElement(field) for field in form])

    @abc.abstractmethod
    async def apply(self, request: Request, form: Form) -> Response:
        ...

    async def dispatch(self, request: Request) -> Response:
        form = await self.get_form_class().from_request(request)
        if await form.validate_on_submit(request):
            return await self.apply(request, form)

        layout = self.get_form_layout(form)
        return render_to_response(
            request,
            'ohmyadmin/actions/placeholder.html',
            {
                'request': request,
                'action': self,
                'layout': layout,
            },
        )

    def dismiss(self, message: str = '', category: FlashCategory = 'success') -> Response:
        response = Response.empty().hx_event(DISMISS_EVENT)
        if message:
            response = response.hx_toast(message, category)
        return response


class BoundAction:
    def __init__(self, action: Action, url: str) -> None:
        self.action = action
        self.url = url


class ActionResponse:
    class Type(str, enum.Enum):
        TOAST = 'toast'
        REDIRECT = 'redirect'
        REFRESH = 'refresh'

    @dataclasses.dataclass
    class ToastOptions:
        message: str
        category: FlashCategory

    @dataclasses.dataclass
    class RedirectOptions:
        url: str | None = None
        path_name: str | None = None
        path_params: typing.Mapping[str, str | int] | None = None
        resource: typing.Type[Resource] | Resource | None = None
        resource_action: ResourceAction = 'list'

    def __init__(
        self, type: str, toast_options: ToastOptions | None = None, redirect_options: RedirectOptions | None = None
    ) -> None:
        self.type = type
        self.toast_options = toast_options
        self.redirect_options = redirect_options

    def with_success(self, message: str) -> ActionResponse:
        self.toast_options = self.ToastOptions(message=message, category='success')
        return self

    def with_error(self, message: str) -> ActionResponse:
        self.toast_options = self.ToastOptions(message=message, category='error')
        return self

    @classmethod
    def toast(cls, message: str, category: FlashCategory = 'success') -> ActionResponse:
        return ActionResponse(type=cls.Type.TOAST, toast_options=cls.ToastOptions(message=message, category=category))

    @classmethod
    def redirect(cls, url: str) -> ActionResponse:
        return ActionResponse(type=cls.Type.REDIRECT, redirect_options=cls.RedirectOptions(url=url))

    @classmethod
    def redirect_to_path_name(
        cls, path_name: str | None = None, path_params: typing.Mapping[str, str | int] | None = None
    ) -> ActionResponse:
        return ActionResponse(
            type=cls.Type.REDIRECT,
            redirect_options=cls.RedirectOptions(path_name=path_name, path_params=path_params or {}),
        )

    @classmethod
    def redirect_to_resource(
        cls,
        resource: typing.Type[Resource] | Resource,
        action: ResourceAction = 'list',
    ) -> ActionResponse:
        return ActionResponse(
            type=cls.Type.REDIRECT,
            redirect_options=cls.RedirectOptions(
                resource=resource,
                resource_action=action,
            ),
        )

    @classmethod
    def refresh(cls) -> ActionResponse:
        return ActionResponse(type=cls.Type.REFRESH)
