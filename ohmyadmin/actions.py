from __future__ import annotations

import abc
import typing
from slugify import slugify
from starlette.datastructures import URL
from starlette.requests import Request

from ohmyadmin.components import ButtonColor
from ohmyadmin.helpers import camel_to_sentence
from ohmyadmin.templating import macro

DISMISS_EVENT = 'modals.dismiss'


class Action:
    slug: typing.ClassVar[str] = ''

    def __init_subclass__(cls, **kwargs: typing.Any) -> None:
        cls.slug = slugify(camel_to_sentence(cls.__name__))

    def __init__(self, label: str, icon: str = '') -> None:
        self.icon = icon
        self.label = label


class LinkAction(Action):
    def __init__(self, url: str | URL, label: str, icon: str = '', color: ButtonColor = 'default') -> None:
        super().__init__(label=label, icon=icon)
        self.url = str(url)
        self.color = color

    def render(self, request: Request) -> str:
        m = macro('ohmyadmin/lib/buttons.html', 'link_button')
        return m(text=self.label, icon=self.icon, color=self.color, url=self.url)


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


class BatchAction:
    icon: str = ''
    label: str = ''

    def __init__(self, label: str = '', icon: str = '') -> None:
        self.icon = icon or self.icon
        self.label = label or self.label


# class BaseAction2(Component, abc.ABC):
#     id: typing.ClassVar[str] = ''
#     label: typing.ClassVar[str] = ''
#     title: typing.ClassVar[str] = _('Do you want to run this action?')
#     message: typing.ClassVar[str] = ''
#     icon: typing.ClassVar[str] = ''
#     dangerous: typing.ClassVar[bool] = False
#     color: typing.ClassVar[ButtonColor] = 'default'
#     template: str = 'ohmyadmin/components/action.html'
#
#     @abc.abstractmethod
#     async def dispatch(self, request: Request) -> Response:
#         ...
#
#     @property
#     def url(self) -> str:
#         request = get_current_request()
#         if request.state.resource:
#             return request.url_for(request.state.resource.get_route_name('action'), action_id=self.id)
#
#         raise ValueError('Action called from unknown context.')
#
#     def dismiss(self, message: str = '', category: FlashCategory = 'success') -> Response:
#         response = Response.empty().hx_event(DISMISS_EVENT)
#         if message:
#             response = response.hx_toast(message, category)
#         return response
#
#     async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
#         response = await self.dispatch(Request(scope, receive, send))
#         await response(scope, receive, send)
#
#
# class FormActionMixin:
#     form_class: typing.ClassVar[typing.Type[Form]] = Form
#
#     def get_form_class(self) -> typing.Type[Form]:
#         return getattr(self, 'ActionForm', self.form_class)
#
#     def get_form_layout(self, form: Form) -> Component:
#         return Grid(columns=1, children=[FormElement(field, horizontal=True) for field in form])
#
#
# class Action2(Action, FormActionMixin):
#     @abc.abstractmethod
#     async def apply(self, request: Request, form: Form) -> Response:
#         ...
#
#     async def dispatch(self, request: Request) -> Response:
#         form = await self.get_form_class().from_request(request)
#         if await form.validate_on_submit(request):
#             return await self.apply(request, form)
#
#         layout = self.get_form_layout(form)
#         return render_to_response(
#             request,
#             'ohmyadmin/actions/action.html',
#             {
#                 'request': request,
#                 'action': self,
#                 'layout': layout,
#             },
#         )
#
#
# class BatchAction2(Action, FormActionMixin):
#     coerce: typing.Callable = int
#     template: str = ''
#
#     @property
#     def url(self) -> str:
#         request = get_current_request()
#         if request.state.resource:
#             return request.url_for(request.state.resource.get_route_name('batch'), action_id=self.id)
#
#         raise ValueError('Action called from unknown context.')
#
#     @abc.abstractmethod
#     async def apply(self, request: Request, ids: list[PkType], form: Form) -> Response:
#         ...
#
#     async def dispatch(self, request: Request) -> Response:
#         form = await self.get_form_class().from_request(request)
#         object_ids = [
#             self.coerce(typing.cast(str, object_id)) for object_id in request.query_params.getlist('selected')
#         ]
#         if await form.validate_on_submit(request):
#             return await self.apply(request, object_ids, form)
#
#         layout = self.get_form_layout(form)
#         return render_to_response(
#             request,
#             'ohmyadmin/actions/batch_action.html',
#             {
#                 'request': request,
#                 'action': self,
#                 'layout': layout,
#                 'object_ids': object_ids,
#             },
#         )
#
#
# class BulkDeleteAction2(BatchAction2):
#     dangerous = True
#     message = _('Do you want to delete all items?')
#
#     async def apply(self, request: Request, ids: list[PkType], form: Form) -> Response:
#         stmt = sa.select(request.state.resource.entity_class).where(
#             sa.column(request.state.resource.pk_column).in_(ids)
#         )
#         result = await request.state.dbsession.scalars(stmt)
#         for row in result.all():
#             await request.state.dbsession.delete(row)
#         await request.state.dbsession.commit()
#
#         return Response.empty().hx_redirect(URLSpec.to_resource(request.state.resource))
