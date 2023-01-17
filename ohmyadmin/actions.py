from __future__ import annotations

import dataclasses

import abc
import json
import typing
import wtforms
from starlette.background import BackgroundTask
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response
from starlette_babel import gettext_lazy as _

from ohmyadmin.forms import create_form, validate_on_submit
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

        if isinstance(callback, FormModal):
            self.hx_target = '#modals'

    def render(self, request: Request) -> str:
        menu_link = request.url.include_query_params(_action=self.slug)
        return render_to_string(request, self.template, {'action': self, 'menu_link': menu_link})

    async def dispatch(self, request: Request) -> Response:
        return await self.callback(request)


@dataclasses.dataclass
class FormModal:
    title: str
    callback: ModalActionCallback
    form_class: type[wtforms.Form]
    message: str = ''
    actions: typing.Sequence[Submit] | None = None
    template: str = 'ohmyadmin/actions/modal.html'

    def __post_init__(self) -> None:
        self.actions = self.actions or [
            Submit(_('Submit', domain='ohmyadmin'), variant='accent'),
            Submit(
                _('Cancel', domain='ohmyadmin'),
                variant='text',
                type='button',
                html_attrs={
                    '@click': 'closeModal;',
                },
            ),
        ]

    async def dispatch(self, request: Request) -> Response:
        form = await create_form(request, self.form_class)
        if await validate_on_submit(request, form):
            return await self.handle(request, form)
        return render_to_response(request, self.template, {'modal': self, 'form': form})

    async def handle(self, request: Request, form: wtforms.Form) -> ActionResponse:
        return await self.callback(request, form)

    async def default_callback(self, request: Request, form: wtforms.Form) -> ActionResponse:
        return ActionResponse().show_toast('Modal action has no callback.', 'error')

    async def __call__(self, request: Request) -> Response:
        return await self.dispatch(request)


class BatchDelete:
    title = _('Delete multiple objects', domain='ohmyadmin')
    message = _('Are you sure you want to delete selected objects?', domain='ohmyadmin')
    dangerous = True


#
#     async def apply(self, request: Request, form: wtforms.Form, object_ids: list[str]) -> Response:
#         datasource: DataSource = request.state.datasource
#         await datasource.delete(*object_ids)
#         return ActionResponse().show_toast(_('Objects has been deleted.', domain='ohmyadmin')).close_modal()

# def render_menu_item(self, request: Request, obj: typing.Any) -> str:
#     params = MultiDict(parse_qsl(request.url.query, keep_blank_values=True))
#     params.append('_action', self.slug)
#     params.setlist('_ids', [obj.id])  # FIXME: unhardcode .id
#     menu_link = request.url.replace(query=urlencode(params.multi_items()))
#     return render_to_string(
#         request,
#         self.menu_template,
#         {
#             'action': self,
#             'object': obj,
#             'menu_link': menu_link,
#         },
#     )

# async def parse_object_ids(self, request: Request) -> list[str]:
#     object_ids = request.query_params.getlist('_ids')
#     if not object_ids and request.method != 'GET':
#         form_data = await request.form()
#         object_ids = typing.cast(list[str], form_data.getlist('_ids'))
#     return object_ids

# def render(self, request: Request) -> str:
#     params = MultiDict(parse_qsl(request.url.query, keep_blank_values=True))
#     params.append('_action', self.slug)
#     params.setlist('_ids', [])
#     menu_link = request.url.replace(query=urlencode(params.multi_items()))
#     return render_to_string(request, self.template, {'action': self, 'menu_link': menu_link})
