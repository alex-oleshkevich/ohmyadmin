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
from ohmyadmin.forms import create_form, validate_on_submit
from ohmyadmin.helpers import LazyURL, resolve_url
from ohmyadmin.shortcuts import render_to_response, render_to_string

ButtonType = typing.Literal['default', 'accent', 'primary', 'danger', 'warning', 'success', 'text', 'link']
RequestMethod = typing.Literal['get', 'post', 'patch', 'put', 'delete']
ObjectURLFactory = typing.Callable[[Request, typing.Any], URL | str]


class ActionError(Exception):
    ...


class UndefinedActionError(ActionError):
    ...


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


response = ActionResponse

ActionCallback = typing.Callable[[Request], typing.Awaitable[Response]]


class PageAction(abc.ABC):
    template: str = ''

    def render(self, request: Request) -> str:
        assert self.template, f'template is not defined on class {self.__class__.__name__}'
        return render_to_string(request, self.template, {'action': self})


class Link(PageAction):
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


class Submit(PageAction):
    """
    Submit actions are regular buttons.

    Mostly for use with forms.
    """

    template = 'ohmyadmin/actions/submit.html'

    def __init__(
        self,
        label: str,
        variant: ButtonType = 'default',
        name: str = '',
        html_attrs: typing.Mapping[str, typing.Any] | None = None,
        type: typing.Literal['button', 'submit'] = 'submit',
    ) -> None:
        self.name = name
        self.label = label
        self.type = type
        self.variant = variant
        self.html_attrs = html_attrs or {}


class Dispatch(abc.ABC):  # pragma: no cover
    slug: str

    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:
        ...


class Callback(Dispatch, PageAction):
    """Callback actions execute a backend function when clicked."""

    template = 'ohmyadmin/actions/callback.html'

    def __init__(
        self,
        slug: str,
        label: str,
        callback: ActionCallback,
        icon: str = '',
        variant: ButtonType = 'default',
        confirmation: str = '',
        http_method: RequestMethod = 'get',
        hx_target: str = '',
    ) -> None:
        self.icon = icon
        self.label = label
        self.http_method = http_method
        self.callback = callback
        self.hx_target = hx_target
        self.variant = variant
        self.confirmation = confirmation
        self.slug = slug

    def render(self, request: Request) -> str:
        menu_link = request.url.include_query_params(_action=self.slug)
        return render_to_string(request, self.template, {'action': self, 'menu_link': menu_link})

    async def dispatch(self, request: Request) -> Response:
        return await self.callback(request)


class ObjectAction(abc.ABC):
    template: str = ''

    def render(self, request: Request, obj: typing.Any) -> str:
        assert self.template, f'template is not defined on class {self.__class__.__name__}'
        return render_to_string(request, self.template, {'action': self, 'object': obj})


class ObjectLink(ObjectAction):
    """Renders as a dropdown menu item."""

    template = 'ohmyadmin/actions/object_link.html'

    def __init__(self, label: str, url: str | LazyURL | ObjectURLFactory, icon: str = '') -> None:
        self.url = url
        self.icon = icon
        self.label = label

    def resolve(self, request: Request, obj: typing.Any) -> URL:
        if isinstance(self.url, (str, LazyURL)):
            return resolve_url(request, self.url)
        return URL(str(self.url(request, obj)))


class ObjectCallback(Dispatch, ObjectAction):
    """
    Renders as dropdown menu item.

    When clicked, dispatches AJAX call to API.
    """

    slug: str = ''
    template = 'ohmyadmin/actions/object_callback.html'

    def __init__(
        self,
        slug: str,
        label: str,
        callback: ActionCallback,
        icon: str = '',
        dangerous: bool = False,
        http_method: RequestMethod = 'get',
        confirmation: str = '',
    ) -> None:
        self.slug = slug
        self.icon = icon
        self.label = label
        self.http_method = http_method
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


class BasePageAction(Callback):
    icon: str = ''
    button_color: ButtonType = 'default'
    label: str = '<unlabeled>'
    confirmation: str = ''
    method: RequestMethod = 'get'
    slug: str = ''

    def __init__(self, slug: str = '') -> None:
        slug = slug or self.slug or slugify(self.__class__.__name__.removesuffix('PageAction'))
        super().__init__(
            slug,
            label=self.label,
            callback=self.dispatch,
            icon=self.icon,
            variant=self.button_color,
            confirmation=self.confirmation,
            http_method=self.method,
            hx_target='#modals',
        )

    @abc.abstractmethod
    async def apply(self, request: Request) -> Response:  # pragma: no cover
        ...

    async def dispatch(self, request: Request) -> Response:
        return await self.apply(request)


class BaseFormPageAction(BasePageAction):
    form_class: type[wtforms.Form] = wtforms.Form
    actions: list[Submit | Link] | None = None
    form_template: str = 'ohmyadmin/actions/form_action.html'

    async def get_form_object(self, request: Request) -> typing.Any:
        return None

    def get_form_actions(self, request: Request, model: typing.Any) -> list[Submit | Link]:
        return self.actions or [
            Submit(label=_('Submit', domain='ohmyadmin'), variant='accent', type='submit'),
            Submit(
                label=_('Cancel', domain='ohmyadmin'),
                variant='text',
                type='button',
                html_attrs={
                    '@click': 'closeModal;',
                },
            ),
        ]

    async def apply(self, request: Request) -> Response:
        model = await self.get_form_object(request)
        form = await create_form(request, self.form_class, model)
        if await validate_on_submit(request, form):
            return await self.handle(request, form, model)

        return render_to_response(
            request,
            self.form_template,
            {'action': self, 'form': form, 'actions': self.get_form_actions(request, model)},
        )

    @abc.abstractmethod
    async def handle(self, request: Request, form: wtforms.Form, model: typing.Any) -> Response:  # pragma: no cover
        ...


class BaseObjectAction(ObjectCallback):
    icon: str = ''
    label: str = '<unlabeled>'
    dangerous: bool = False
    confirmation: str = ''
    http_method: RequestMethod = 'get'

    def __init__(self, slug: str = '') -> None:
        slug = slug or self.slug or slugify(self.__class__.__name__.removesuffix('ObjectAction'))
        super().__init__(
            slug,
            label=self.label,
            callback=self.dispatch,
            icon=self.icon,
            dangerous=self.dangerous,
            http_method=self.http_method,
            confirmation=self.confirmation,
        )

    @abc.abstractmethod
    async def apply(self, request: Request, object_id: str) -> Response:  # pragma: no cover
        ...

    async def dispatch(self, request: Request) -> Response:
        object_id = request.query_params.get('_ids', '')
        if not object_id:
            return ActionResponse().show_toast(_('No object selected.', domain='ohmyadmin'), 'error')
        return await self.apply(request, object_id)


class BaseFormObjectAction(BaseObjectAction):
    form_class: type[wtforms.Form] = wtforms.Form
    actions: list[Submit | Link] | None = None
    form_template: str = 'ohmyadmin/actions/form_action.html'

    async def get_form_object(self, request: Request, object_id: str) -> typing.Any:
        return None

    def get_form_actions(self, request: Request, model: typing.Any) -> list[Submit | Link]:
        return self.actions or [
            Submit(label=_('Submit', domain='ohmyadmin'), variant='accent', type='submit'),
            Submit(
                label=_('Cancel', domain='ohmyadmin'),
                variant='text',
                type='button',
                html_attrs={
                    '@click': 'closeModal;',
                },
            ),
        ]

    async def apply(self, request: Request, object_id: str) -> Response:
        model = await self.get_form_object(request, object_id)
        form = await create_form(request, self.form_class, model)
        if await validate_on_submit(request, form):
            return await self.handle(request, form, model)

        return render_to_response(
            request,
            self.form_template,
            {'action': self, 'form': form, 'actions': self.get_form_actions(request, model)},
        )

    @abc.abstractmethod
    async def handle(self, request: Request, form: wtforms.Form, model: typing.Any) -> Response:  # pragma: no cover
        ...


class BatchAction(ObjectCallback, abc.ABC):
    slug: str = ''

    @abc.abstractmethod
    async def apply(self, request: Request, object_ids: list[str], form: wtforms.Form) -> Response:  # pragma: no cover
        ...


class BaseBatchAction(BatchAction):
    label: str = '<unlabeled>'
    dangerous: bool = False
    message: str = _('Do you really want to appy this action on selected rows?', domain='ohmyadmin')
    form_class: type[wtforms.Form] = wtforms.Form
    template = 'ohmyadmin/actions/batch_action_modal.html'

    def __init__(self, slug: str = '') -> None:
        slug = slug or self.slug or slugify(self.__class__.__name__.removesuffix('BatchAction'))
        super().__init__(
            slug=slug, label=self.label, callback=self.dispatch, dangerous=self.dangerous, http_method='get'
        )

    async def dispatch(self, request: Request) -> Response:
        object_ids = request.query_params.getlist('_ids')
        form = await create_form(request, self.form_class)
        if await validate_on_submit(request, form):
            return await self.apply(request, object_ids, form)
        return render_to_response(request, self.template, {'object_ids': object_ids, 'action': self, 'form': form})


class BatchDelete(BaseBatchAction):
    dangerous = True
    success_message = _('{count} records has been deleted.', domain='ohmyadmin')
    message = _('Are you sure you want to delete selected objects?', domain='ohmyadmin')
    label = _('Mass delete', domain='ohmyadmin')

    async def apply(self, request: Request, object_ids: list[str], form: wtforms.Form) -> Response:
        datasource: DataSource = request.state.datasource
        await datasource.delete(request, *object_ids)
        return ActionResponse().show_toast(self.success_message.format(count=len(object_ids))).close_modal()


class DeleteObjectAction(BaseObjectAction):
    icon = 'trash'
    dangerous = True
    label = _('Delete', domain='ohmyadmin')
    success_message = _('{object} has been deleted.', domain='ohmyadmin')
    confirmation = _('Are you sure you want to delete this record?', domain='ohmyadmin')
    http_method = 'delete'

    async def apply(self, request: Request, object_id: str) -> Response:
        if request.method in ['POST', 'DELETE']:
            datasource: DataSource = request.state.datasource
            model = await datasource.get(request, object_id)
            await datasource.delete(request, object_id)
            return ActionResponse().show_toast(self.success_message.format(object=model)).refresh_datatable()
        return ActionResponse().show_toast(_('Unsupported HTTP method.'), 'error')
