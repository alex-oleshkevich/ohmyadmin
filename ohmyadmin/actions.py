from __future__ import annotations

import abc
import json
import typing
import wtforms
from starlette.background import BackgroundTask
from starlette.datastructures import URL, MultiDict
from starlette.requests import Request
from starlette.responses import Response
from starlette_babel import gettext_lazy as _
from urllib.parse import parse_qsl, urlencode

from ohmyadmin.helpers import LazyURL, resolve_url
from ohmyadmin.shortcuts import render_to_response, render_to_string

ButtonType = typing.Literal['default', 'accent', 'primary', 'danger', 'warning', 'success', 'text', 'link']
RequestMethod = typing.Literal['get', 'post', 'patch', 'put', 'delete']


class ActionResponse(Response):
    def __init__(
        self,
        status_code: int = 204,
        headers: dict[str, typing.Any] | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        super().__init__(status_code=status_code, headers=headers, background=background)

    def show_toast(self, message: str, category: typing.Literal['success', 'error'] = 'success') -> ActionResponse:
        return self.trigger('toast', {'message': str(message), 'category': category})

    def redirect(self, request: Request, url: str | LazyURL) -> ActionResponse:
        """Triggers a client-side redirect to a new location."""
        self.headers['hx-redirect'] = str(url.resolve(request)) if isinstance(url, LazyURL) else url
        return self

    def refresh(self) -> ActionResponse:
        """Trigger full refresh of the page."""
        self.headers['hx-refresh'] = 'true'
        return self

    def refresh_datatable(self) -> ActionResponse:
        return self.trigger('refresh-datatable')

    def close_modal(self) -> ActionResponse:
        return self.trigger('modals.close')

    def trigger(self, event: str, data: str | dict[str, str | float] = '') -> ActionResponse:
        payload = json.loads(self.headers.get('hx-trigger', '{}'))
        payload[event] = data
        self.headers['hx-trigger'] = json.dumps(payload)
        return self


ActionCallback = typing.Callable[[Request], typing.Awaitable[ActionResponse]]
ModalActionCallback = typing.Callable[[Request, wtforms.Form], typing.Awaitable[ActionResponse]]


class Action(abc.ABC):
    template: str = ''

    def render(self, request: Request) -> str:
        assert self.template, f'template is not defined on class {self.__class__.__name__}'
        return render_to_string(request, self.template, {'action': self})


class Link(Action):
    """
    A link action.

    Can point to anywhere.
    """

    template = 'ohmyadmin/actions/link.html'

    def __init__(self, label: str, url: str | LazyURL, icon: str = '', variant: ButtonType = 'link') -> None:
        self.url = url
        self.icon = icon
        self.label = label
        self.variant = variant
        self.slug = '-----'

    def resolve(self, request: Request) -> URL:
        return resolve_url(request, self.url)


class Submit(Action):
    """
    Submit actions are regular buttons.

    Mostly for use with forms.
    """

    template = 'ohmyadmin/actions/submit.html'

    def __init__(
        self,
        label: str,
        variant: ButtonType,
        name: str = '',
        html_attrs: typing.Mapping[str, typing.Any] | None = None,
        type: typing.Literal['button', 'submit'] = 'submit',
    ) -> None:
        self.name = name
        self.label = label
        self.type = type
        self.variant = variant
        self.html_attrs = html_attrs or {}


class Dispatch(abc.ABC):
    slug: str

    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:
        ...


class Callback(Dispatch, Action):
    """Callback actions execute a backend function when clicked."""

    template = 'ohmyadmin/actions/callback.html'

    def __init__(
        self,
        slug: str,
        label: str,
        callback: ActionCallback,
        icon: str = '',
        color: ButtonType = 'default',
        confirmation: str = '',
        method: RequestMethod = 'get',
        hx_target: str = '',
    ) -> None:
        self.icon = icon
        self.label = label
        self.method = method
        self.callback = callback
        self.hx_target = hx_target
        self.color = color
        self.confirmation = confirmation
        self.slug = slug

        if isinstance(callback, Modal):
            self.hx_target = '#modals'

    def render(self, request: Request) -> str:
        menu_link = request.url.include_query_params(_action=self.slug)
        return render_to_string(request, self.template, {'action': self, 'menu_link': menu_link})

    async def dispatch(self, request: Request) -> Response:
        return await self.callback(request)


class Modal(abc.ABC):
    title: str = ''
    template: str = 'ohmyadmin/actions/modal.html'

    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:
        ...

    def render(self, request: Request, context: typing.Mapping[str, typing.Any] | None = None) -> Response:
        context = dict(context or {})
        context.setdefault('modal', self)
        return render_to_response(request, self.template, context)

    async def __call__(self, request: Request) -> Response:
        return await self.dispatch(request)


class ObjectAction:
    template: str = ''

    def render(self, request: Request, object: typing.Any) -> str:
        assert self.template
        return render_to_string(request, self.template, {'action': self, 'object': object})


ObjectURLFactory = typing.Callable[[Request, typing.Any], URL | str]


class ObjectLink(ObjectAction):
    template = 'ohmyadmin/actions/object_link.html'

    def __init__(self, label: str, url: str | LazyURL | ObjectURLFactory, icon: str = '') -> None:
        self.url = url
        self.icon = icon
        self.label = label

    def resolve(self, request: Request, object: typing.Any) -> URL:
        if isinstance(self.url, (str, LazyURL)):
            return resolve_url(request, self.url)
        return URL(str(self.url(request, object)))


class ObjectCallback(Dispatch, ObjectAction):
    template = 'ohmyadmin/actions/object_callback.html'

    def __init__(
        self,
        slug: str,
        label: str,
        callback: ActionCallback,
        icon: str = '',
        dangerous: bool = False,
        method: RequestMethod = 'get',
        confirmation: str = '',
    ) -> None:
        self.slug = slug
        self.icon = icon
        self.label = label
        self.method = method
        self.callback = callback
        self.dangerous = dangerous
        self.confirmation = confirmation

    def resolve_url(self, request: Request, obj: typing.Any) -> URL:
        params = MultiDict(parse_qsl(request.url.query, keep_blank_values=True))
        params.append('_object_action', self.slug)
        params.setlist('_ids', [request.state.datasource.get_pk(obj)])
        return request.url.replace(query=urlencode(params.multi_items()))

    async def dispatch(self, request: Request) -> Response:
        return await self.callback(request)


class BatchDelete:
    title = _('Delete multiple objects', domain='ohmyadmin')
    message = _('Are you sure you want to delete selected objects?', domain='ohmyadmin')
    dangerous = True
