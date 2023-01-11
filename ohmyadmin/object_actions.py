import abc
import typing
from urllib.parse import parse_qsl, urlencode

import wtforms
from slugify import slugify
from starlette.datastructures import MultiDict
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.helpers import camel_to_sentence, get_callable_name, LazyURL, resolve_url
from ohmyadmin.responses import ActionResponse
from ohmyadmin.shortcuts import render_to_response, render_to_string


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

    def resolve(self, request: Request) -> str:
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
        return render_to_string(request, self.template, {
            'action': self, 'object': obj, 'menu_link': menu_link, 'hx_target': self.hx_target,
        })

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

    async def dispatch(self, request: Request) -> Response:
        model_instance = await self.get_object(request)
        form_data = await request.form() if request.method not in ['GET', 'HEAD'] else None
        form = self.form_class(formdata=form_data, obj=model_instance)

        if request.method == 'POST' and form.validate():
            return await self.handle_submit(request, form, model_instance)

        return render_to_response(request, self.content_template, {
            'modal': self, 'form': form, 'object': model_instance,
        })

    async def handle_submit(self, request: Request, form: wtforms.Form, instance: typing.Any | None) -> Response:
        return ActionResponse().close_modal()

    async def __call__(self, request: Request) -> Response:
        return await self.dispatch(request)


class Modal(Dispatch):

    def __init__(
        self, label: str, modal: ModalAction, icon: str = '', dangerous: bool = False, confirmation: str = '',
        slug: str = '',
    ) -> None:
        super().__init__(
            label=label, callback=modal, icon=icon, dangerous=dangerous, confirmation=confirmation, method='get',
            slug=slug, hx_target='#modals',
        )
        self.modal = modal
