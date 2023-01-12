from __future__ import annotations

import abc
import json
import typing
import wtforms
from slugify import slugify
from starlette.background import BackgroundTask
from starlette.datastructures import URL, MultiDict
from starlette.requests import Request
from starlette.responses import Response
from urllib.parse import parse_qsl, urlencode

from ohmyadmin.helpers import LazyURL, camel_to_sentence, get_callable_name, resolve_url
from ohmyadmin.shortcuts import render_to_response, render_to_string


class ActionResponse(Response):
    def __init__(
        self,
        status_code: int = 204,
        headers: dict[str, typing.Any] | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        super().__init__(status_code=status_code, headers=headers, background=background)

    def show_toast(self, message: str, category: typing.Literal['success', 'error'] = 'success') -> ActionResponse:
        return self.trigger('toast', {'message': message, 'category': category})

    def redirect(self, request: Request, url: str | LazyURL) -> ActionResponse:
        """Triggers a client-side redirect to a new location."""
        self.headers['hx-redirect'] = url.resolve(request) if isinstance(url, LazyURL) else url
        return self

    def refresh(self, request: Request, url: str | LazyURL) -> ActionResponse:
        """Trigger full refresh of the page."""
        self.headers['hx-refresh'] = url.resolve(request) if isinstance(url, LazyURL) else url
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


class ObjectAction(abc.ABC):
    label: str = ''
    icon: str = ''
    confirmation: str = ''
    template: str = ''
    method: typing.Literal['get', 'post', 'put', 'patch', 'delete']
    dangerous: bool = False

    def render_menu_item(self, request: Request, obj: typing.Any) -> str:
        return render_to_string(request, self.template, {'action': self})

    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:
        ...


class Link(ObjectAction):
    template = 'ohmyadmin/object_actions/object_action_link.html'

    def __init__(self, label: str, url: str | LazyURL, icon: str = '', dangerous: bool = False) -> None:
        self.url = url
        self.icon = icon
        self.label = label
        self.dangerous = dangerous
        self.slug = '-----'

    def resolve(self, request: Request) -> URL:
        return resolve_url(request, self.url)

    async def dispatch(self, request: Request) -> Response:
        raise NotImplementedError('Link action cannot be dispatched.')


class Dispatch(ObjectAction):
    template = 'ohmyadmin/object_actions/object_action_dispatch.html'

    def __init__(
        self,
        label: str,
        callback: typing.Callable[[Request], typing.Awaitable[Response]],
        icon: str = '',
        dangerous: bool = False,
        confirmation: str = '',
        slug: str = '',
        method: typing.Literal['get', 'post', 'patch', 'put', 'delete'] = 'get',
        hx_target: str = '',
    ) -> None:
        self.method = method
        self.callback = callback
        self.slug = slug or slugify(camel_to_sentence(get_callable_name(callback)))
        self.icon = icon or self.icon
        self.label = label or self.label
        self.hx_target = hx_target
        self.dangerous = dangerous or self.dangerous
        self.confirmation = confirmation or self.confirmation

    def render_menu_item(self, request: Request, obj: typing.Any) -> str:
        params = MultiDict(parse_qsl(request.url.query, keep_blank_values=True))
        params.append('_action', self.slug)
        params.setlist('_ids', [obj.id])  # FIXME: .id must not be hardcoded
        menu_link = request.url.replace(query=urlencode(params.multi_items()))
        return render_to_string(
            request,
            self.template,
            {
                'action': self,
                'object': obj,
                'menu_link': menu_link,
                'hx_target': self.hx_target,
            },
        )

    async def dispatch(self, request: Request) -> Response:
        return await self.callback(request)


class ModalAction:
    title: str = ''
    dangerous: bool = False
    message: str = ''
    form_class: type[wtforms.Form] = wtforms.Form
    content_template: str = 'ohmyadmin/object_actions/modal_content.html'

    async def get_object(self, request: Request) -> typing.Any | None:
        return None

    async def render_form(self, request: Request) -> Response:
        model = await self.get_object(request)
        form = self.form_class(obj=model)
        return render_to_response(request, self.content_template, {'modal': self, 'form': form, 'object': model})

    async def handler(self, request: Request) -> Response:
        model = await self.get_object(request)
        form = self.form_class(formdata=await request.form(), obj=model)
        if form.validate():
            return await self.handle_submit(request, form, model)
        return render_to_response(request, self.content_template, {'modal': self, 'form': form, 'object': model})

    async def handle_submit(self, request: Request, form: wtforms.Form, instance: typing.Any | None) -> Response:
        return ActionResponse().close_modal()

    async def dispatch(self, request: Request) -> Response:
        if request.method == 'GET':
            return await self.render_form(request)
        return await self.handler(request)

    async def __call__(self, request: Request) -> Response:
        return await self.dispatch(request)


class Modal(Dispatch):
    def __init__(
        self,
        label: str,
        modal: ModalAction,
        icon: str = '',
        dangerous: bool = False,
        confirmation: str = '',
        slug: str = '',
    ) -> None:
        super().__init__(
            label=label,
            callback=modal,
            icon=icon,
            dangerous=dangerous,
            confirmation=confirmation,
            method='get',
            slug=slug,
            hx_target='#modals',
        )
        self.modal = modal
