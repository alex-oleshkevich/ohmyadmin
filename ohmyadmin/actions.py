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
from starlette_babel import gettext_lazy as _
from urllib.parse import parse_qsl, urlencode

from ohmyadmin.datasource.base import DataSource
from ohmyadmin.forms import create_form, validate_form
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
        return self.trigger('toast', {'message': str(message), 'category': category})

    def redirect(self, request: Request, url: str | LazyURL) -> ActionResponse:
        """Triggers a client-side redirect to a new location."""
        self.headers['hx-redirect'] = str(url.resolve(request)) if isinstance(url, LazyURL) else url
        return self

    def refresh(self, request: Request, url: str | LazyURL) -> ActionResponse:
        """Trigger full refresh of the page."""
        self.headers['hx-refresh'] = str(url.resolve(request)) if isinstance(url, LazyURL) else url
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


class Action(abc.ABC):
    label: str = ''
    icon: str = ''
    confirmation: str = ''
    method: typing.Literal['get', 'post', 'put', 'patch', 'delete']
    dangerous: bool = False
    menu_template: str = ''
    template: str = ''

    def render_menu_item(self, request: Request, obj: typing.Any) -> str:
        return render_to_string(request, self.menu_template, {'action': self})

    def render(self, request: Request) -> str:
        assert self.template, f'button_template is not defined on class {self.__class__.__name__}'
        return render_to_string(request, self.template, {'action': self})

    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:
        ...


class Link(Action):
    menu_template = 'ohmyadmin/actions/link_menu_item.html'
    template = 'ohmyadmin/actions/link.html'

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


class Submit(Action):
    template = 'ohmyadmin/actions/submit.html'

    def __init__(
        self,
        label: str,
        variant: typing.Literal['', 'accent', 'primary', 'danger', 'success', 'warning'],
        name: str = '',
    ) -> None:
        self.name = name
        self.label = label
        self.variant = variant

    def render_menu_item(self, request: Request, obj: typing.Any) -> str:
        raise NotImplementedError('Submit actions cannot be used as menu items.')

    def resolve(self, request: Request) -> URL:
        raise NotImplementedError('Submit actions have no URLs.')

    async def dispatch(self, request: Request) -> Response:
        raise NotImplementedError('Submit action cannot be dispatched.')


class Callback(Action):
    menu_template = 'ohmyadmin/actions/callback_menu_item.html'
    template = 'ohmyadmin/actions/callback.html'

    def __init__(
        self,
        label: str,
        callback: typing.Callable[[Request, list[str]], typing.Awaitable[Response]],
        icon: str = '',
        dangerous: bool = False,
        confirmation: str = '',
        slug: str = '',
        method: typing.Literal['get', 'post', 'patch', 'put', 'delete'] = 'get',
        hx_target: str = '',
    ) -> None:
        self.icon = icon
        self.label = label
        self.method = method
        self.callback = callback
        self.hx_target = hx_target
        self.dangerous = dangerous
        self.confirmation = confirmation
        self.slug = slug or slugify(camel_to_sentence(get_callable_name(callback)))

    def render_menu_item(self, request: Request, obj: typing.Any) -> str:
        params = MultiDict(parse_qsl(request.url.query, keep_blank_values=True))
        params.append('_action', self.slug)
        params.setlist('_ids', [obj.id])  # FIXME: unhardcode .id
        menu_link = request.url.replace(query=urlencode(params.multi_items()))
        return render_to_string(
            request,
            self.menu_template,
            {
                'action': self,
                'object': obj,
                'menu_link': menu_link,
            },
        )

    def render(self, request: Request) -> str:
        params = MultiDict(parse_qsl(request.url.query, keep_blank_values=True))
        params.append('_action', self.slug)
        params.setlist('_ids', [])
        menu_link = request.url.replace(query=urlencode(params.multi_items()))
        return render_to_string(request, self.template, {'action': self, 'menu_link': menu_link})

    async def parse_object_ids(self, request: Request) -> list[str]:
        object_ids = request.query_params.getlist('_ids')
        if not object_ids and request.method != 'GET':
            form_data = await request.form()
            object_ids = typing.cast(list[str], form_data.getlist('_ids'))
        return object_ids

    async def dispatch(self, request: Request) -> Response:
        return await self.callback(request, await self.parse_object_ids(request))


class ModalAction(abc.ABC):
    title: str = ''
    dangerous: bool = False
    message: str = ''
    form_class: type[wtforms.Form] = wtforms.Form
    template: str = 'ohmyadmin/actions/modal.html'

    async def get_form_object(self, request: Request) -> typing.Any | None:
        return None

    async def render_form(self, request: Request, object_ids: list[str]) -> Response:
        model = await self.get_form_object(request)
        form = await create_form(request, self.form_class, model)
        return render_to_response(request, self.template, {'modal': self, 'form': form, 'object': model})

    async def handle_form(self, request: Request, object_ids: list[str]) -> Response:
        model = await self.get_form_object(request)
        form = await create_form(request, self.form_class, model)
        if await validate_form(form):
            return await self.apply(request, form, object_ids)
        return render_to_response(request, self.template, {'modal': self, 'form': form, 'object': model})

    @abc.abstractmethod
    async def apply(self, request: Request, form: wtforms.Form, object_ids: list[str]) -> Response:
        ...

    async def dispatch(self, request: Request, object_ids: list[str]) -> Response:
        if request.method == 'GET':
            return await self.render_form(request, object_ids)
        return await self.handle_form(request, object_ids)

    async def __call__(self, request: Request, object_ids: list[str]) -> Response:
        return await self.dispatch(request, object_ids)


class Modal(Callback):
    def __init__(
        self,
        label: str,
        modal: ModalAction,
        icon: str = '',
        slug: str = '',
    ) -> None:
        super().__init__(
            label=label,
            callback=modal,
            icon=icon,
            dangerous=modal.dangerous,
            method='get',
            slug=slug,
            hx_target='#modals',
        )
        self.modal = modal


class BatchDelete(ModalAction):
    title = _('Delete multiple objects', domain='ohmyadmin')
    message = _('Are you sure you want to delete selected objects?', domain='ohmyadmin')
    dangerous = True

    async def apply(self, request: Request, form: wtforms.Form, object_ids: list[str]) -> Response:
        datasource: DataSource = request.state.datasource
        await datasource.delete(*object_ids)
        return ActionResponse().show_toast('HUI').close_modal()
