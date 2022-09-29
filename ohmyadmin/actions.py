from __future__ import annotations

import abc
import json
import typing
import wtforms
from slugify import slugify
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.components import ButtonColor
from ohmyadmin.flash import FlashCategory
from ohmyadmin.helpers import camel_to_sentence
from ohmyadmin.templating import TemplateResponse, macro

DISMISS_EVENT = 'modals.dismiss'
TOAST_EVENT = 'toast'


class Dispatch(abc.ABC):
    slug: typing.ClassVar[str]

    @abc.abstractmethod
    async def dispatch(self, request: Request) -> Response:
        raise NotImplementedError()


class Action:
    slug: typing.ClassVar[str] = ''

    def __init_subclass__(cls, **kwargs: typing.Any) -> None:
        cls.slug = slugify(camel_to_sentence(cls.__name__.removesuffix('Action')))

    @abc.abstractmethod
    def render(self, request: Request) -> str:
        ...


LinkFactory = typing.Callable[[Request], str]


class LinkAction(Action):
    def __init__(
        self,
        url: str | URL | LinkFactory,
        label: str,
        icon: str = '',
        color: ButtonColor = 'default',
    ) -> None:
        self.label = label
        self.icon = icon
        self.url = url
        self.color = color

    def render(self, request: Request) -> str:
        href = self.url(request) if callable(self.url) else str(self.url)
        macros = macro('ohmyadmin/actions.html', 'link_action')
        return macros(text=self.label, icon=self.icon, color=self.color, url=href)


class RowAction(abc.ABC):
    def __init__(self, text: str = '', icon: str = '') -> None:
        assert text or icon
        self.text = text
        self.icon = icon

    @abc.abstractmethod
    def render(self, request: Request, pk: str, entity: typing.Any) -> str:
        ...


class RowActionGroup(RowAction):
    def __init__(self, actions: list[RowAction], text: str = '', icon: str = 'dots') -> None:
        super().__init__(icon=icon, text=text)
        self.actions = actions

    def render(self, request: Request, pk: str, entity: typing.Any) -> str:
        macros = macro('ohmyadmin/row_actions.html', 'row_action_group')
        return macros(text=self.text, icon=self.icon, actions=self.actions, request=request, pk=pk, entity=entity)


RowLinkFactory = typing.Callable[[Request, str, typing.Any], str]


class LinkRowAction(RowAction):
    def __init__(
        self, url: str | URL | RowLinkFactory, text: str = '', icon: str = '', color: ButtonColor = 'default'
    ) -> None:
        super().__init__(text=text, icon=icon)
        self.url = url
        self.color = color

    def render(self, request: Request, pk: str, entity: typing.Any) -> str:
        href = self.url(request, pk, entity) if callable(self.url) else str(self.url)
        macros = macro('ohmyadmin/row_actions.html', 'link_row_action')
        return macros(text=self.text, icon=self.icon, url=href, color=self.color)


class ModalRowAction(RowAction):
    def __init__(self, action: BatchAction, text: str = '', icon: str = '', color: ButtonColor = 'default') -> None:
        icon = icon or action.icon
        label = text or action.label
        super().__init__(text=label, icon=icon)
        self.action = action
        self.color = color

    def render(self, request: Request, pk: str, entity: typing.Any) -> str:
        macros = macro('ohmyadmin/row_actions.html', 'modal_row_action')
        return macros(text=self.text, icon=self.icon, action=self.action, color=self.color, pk=pk)


class ModalAction(Action, Dispatch):
    label: str = ''
    icon: str = ''
    template: str = 'ohmyadmin/modal_action.html'
    form_class: typing.Type[wtforms.Form] = wtforms.Form

    def __init__(self, label: str = '', icon: str = '', color: ButtonColor = 'default') -> None:
        self.icon = icon or self.icon
        self.label = label or self.label
        self.color = color

    def __init_subclass__(cls, **kwargs: typing.Any) -> None:
        cls.label = camel_to_sentence(cls.__name__.removesuffix('Action'))
        cls.slug = slugify(camel_to_sentence(cls.__name__.removesuffix('Action')))

    @abc.abstractmethod
    async def form_valid(self, request: Request, form: wtforms.Form) -> Response:
        raise NotImplementedError

    def get_form_class(self) -> typing.Type[wtforms.Form]:
        return self.form_class

    async def prefill_form(self, request: Request, form: wtforms.Form) -> None:
        pass

    async def validate_form(self, request: Request, form: wtforms.Form) -> bool:
        return form.validate()

    def dismiss(self, message: str = '', category: FlashCategory = 'success') -> Response:
        events: dict[str, typing.Any] = {DISMISS_EVENT: ''}
        if message:
            events[TOAST_EVENT] = {'message': message, 'category': category}
        return Response(status_code=204, headers={'hx-trigger': json.dumps(events)})

    def refresh(self) -> Response:
        return Response(status_code=204, headers={'hx-refresh': 'true'})

    def redirect(self, url: str | URL) -> Response:
        return Response(status_code=204, headers={'hx-redirect': str(url)})

    async def dispatch(self, request: Request) -> Response:
        object_ids = request.query_params.getlist('object_id')
        form_class = self.get_form_class()
        form_data = await request.form()
        form = form_class(formdata=form_data)
        await self.prefill_form(request, form)

        if request.method == 'POST':
            if await self.validate_form(request, form):
                return await self.form_valid(request, form)

        return TemplateResponse(
            self.template,
            {
                'request': request,
                'action': self,
                'form': form,
                'object_ids': object_ids,
            },
        )

    def render(self, request: Request) -> str:
        macros = macro('ohmyadmin/actions.html', 'modal_action')
        return macros(text=self.label, icon=self.icon, action=self, color=self.color)


class BatchAction(ModalAction):
    label: str = ''
    template: str = 'ohmyadmin/batch_action.html'

    @abc.abstractmethod
    async def apply(self, request: Request, object_ids: list[str], form: wtforms.Form) -> Response:
        raise NotImplementedError()

    async def form_valid(self, request: Request, form: wtforms.Form) -> Response:
        object_ids = request.query_params.getlist('object_id')
        return await self.apply(request, object_ids, form)
