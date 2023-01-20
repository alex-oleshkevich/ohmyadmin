import typing
import wtforms
from starlette.datastructures import URL, FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette.types import Receive, Scope, Send
from starlette_babel import gettext_lazy as _
from starlette_flash import flash

from ohmyadmin import actions
from ohmyadmin.actions import ActionResponse, BatchDelete, DeleteObjectAction
from ohmyadmin.datasource.base import DataSource
from ohmyadmin.forms import create_form, populate_object, validate_on_submit
from ohmyadmin.helpers import LazyObjectURL, LazyURL
from ohmyadmin.pages.base import BasePage
from ohmyadmin.pages.page import Page
from ohmyadmin.pages.pagemixins import HasBatchActions, HasFilters, HasObjectActions, HasPageActions
from ohmyadmin.pages.table import TablePage
from ohmyadmin.views.table import TableColumn


class Resource(BasePage, Router, HasPageActions, HasFilters, HasObjectActions, HasBatchActions):
    group = _('Resources', domain='ohmyadmin')
    datasource: DataSource
    form_class: type[wtforms.Form] = wtforms.Form

    # object list specific
    page_param: typing.ClassVar[str] = 'page'
    page_size_param: typing.ClassVar[str] = 'page_size'
    search_param: typing.ClassVar[str] = 'search'
    ordering_param: typing.ClassVar[str] = 'ordering'
    page_size: typing.ClassVar[int] = 25
    max_page_size: typing.ClassVar[int] = 100
    object_actions: typing.Sequence[actions.ObjectAction] | None = None
    batch_actions: typing.Sequence[actions.BatchAction] | None = None

    # table specific
    columns: typing.Sequence[TableColumn] | None = None

    def __init__(self) -> None:
        super().__init__(routes=self.get_routes())

    def get_table_columns(self, request: Request) -> typing.Sequence[TableColumn]:
        columns = list(self.columns or [])
        for column in columns:
            if column.link is True:
                column.link = LazyObjectURL(
                    lambda r, o: URL(request.url_for(self.get_path_name() + '.edit', pk=self.datasource.get_pk(o)))
                )

        return columns

    def get_page_actions(self, request: Request) -> list[actions.PageAction]:
        create_route_name = self.get_path_name() + '.create'
        page_actions: list[actions.PageAction] = [
            actions.Link(
                label=_('Create', domain='ohmyadmin'),
                url=LazyURL(create_route_name),
                variant='accent',
                icon='plus',
            ),
        ]
        return super().get_page_actions(request) + page_actions

    def get_object_actions(self, request: Request, obj: typing.Any) -> list[actions.ObjectAction]:
        edit_route_name = self.get_path_name() + '.edit'
        object_actions: list[actions.ObjectAction] = [
            actions.ObjectLink(
                label=_('Edit', domain='ohmyadmin'),
                icon='pencil',
                url=LazyURL(path_name=edit_route_name, path_params={'pk': self.datasource.get_pk(obj)}),
            ),
            DeleteObjectAction(),
        ]
        return super().get_object_actions(request, obj) + object_actions

    def get_batch_actions(self, request: Request) -> list[actions.BatchAction]:
        return super().get_batch_actions(request) + [BatchDelete()]

    async def create_form(self, request: Request, model: typing.Any = None) -> wtforms.Form:
        return await create_form(request, self.form_class, model)

    def get_index_page_class(self, request: Request) -> type[Page]:
        class IndexPage(TablePage):
            icon = self.icon
            label = self.label
            label_plural = self.label_plural
            datasource = self.datasource
            page_param = self.page_param
            page_size_param = self.page_size_param
            search_param = self.search_param
            ordering_param = self.ordering_param
            page_size = self.page_size
            max_page_size = self.max_page_size
            columns = self.get_table_columns(request)

            get_filters = self.get_filters
            get_page_actions = self.get_page_actions
            get_object_actions = self.get_object_actions
            get_batch_actions = self.get_batch_actions

        return IndexPage

    def create_empty_model(self, request: Request) -> typing.Any:
        return self.datasource.new()

    async def index_view(self, request: Request) -> Response:
        page_class = self.get_index_page_class(request)
        page_instance = page_class()
        return await page_instance.handler(request)

    def get_create_form_actions(self, request: Request) -> typing.Sequence[actions.Submit | actions.Link]:
        return [
            actions.Submit(label=_('Create and return to list', domain='ohmyadmin'), variant='accent', name='_return'),
            actions.Submit(label=_('Create and edit', domain='ohmyadmin'), name='_edit'),
            actions.Submit(label=_('Create and add new', domain='ohmyadmin'), name='_add_new'),
        ]

    def get_create_view_response(self, request: Request, form_data: FormData, model: typing.Any) -> Response:
        flash(request).success(_('{object} has been created.', domain='ohmyadmin').format(object=model))
        if '_edit' in form_data:
            return ActionResponse().redirect(
                request,
                request.url_for(
                    name=self.get_path_name() + '.edit',
                    pk=self.datasource.get_pk(model),
                ),
            )
        if '_add_new' in form_data:
            return ActionResponse().redirect(request, request.url_for(name=self.get_path_name() + '.create'))
        return ActionResponse().redirect(request, self.generate_url(request))

    async def create_view(self, request: Request) -> Response:
        model = self.create_empty_model(request)
        form = await create_form(request, self.form_class)
        if await validate_on_submit(request, form):
            await populate_object(request, form, model)
            await self.datasource.create(request, model)
            return self.get_create_view_response(request, await request.form(), model)

        form_actions = self.get_create_form_actions(request)
        return self.render_to_response(
            request,
            'ohmyadmin/resources/create.html',
            {
                'page_title': _('Create {label}', domain='ohmyadmin').format(label=self.label),
                'resource': self,
                'form': form,
                'object': model,
                'form_actions': form_actions,
            },
        )

    def get_update_form_actions(self, request: Request) -> typing.Sequence[actions.Submit | actions.Link]:
        return [
            actions.Submit(label=_('Update and return to list', domain='ohmyadmin'), variant='accent', name='_return'),
            actions.Link(label=_('Return to list', domain='ohmyadmin'), url=self.generate_url(request)),
        ]

    def get_update_view_response(self, request: Request, form_data: FormData, model: typing.Any) -> Response:
        flash(request).success(_('{object} has been updated.', domain='ohmyadmin').format(object=model))
        return ActionResponse().redirect(request, self.generate_url(request))

    async def update_view(self, request: Request) -> Response:
        pk = request.path_params['pk']
        model = await self.datasource.get(request, pk)
        form = await create_form(request, self.form_class, model)
        if await validate_on_submit(request, form):
            await populate_object(request, form, model)
            await self.datasource.update(request, model)
            return self.get_update_view_response(request, await request.form(), model)

        form_actions = self.get_update_form_actions(request)
        return self.render_to_response(
            request,
            'ohmyadmin/resources/edit.html',
            {
                'page_title': _('Update {label}', domain='ohmyadmin').format(label=self.label),
                'resource': self,
                'form': form,
                'object': model,
                'form_actions': form_actions,
            },
        )

    async def delete_view(self, request: Request) -> Response:
        pk = request.path_params['pk']
        model = await self.datasource.get(request, pk)
        if request.method in ['POST', 'DELETE']:
            await self.datasource.delete(request, pk)
            flash(request).success(_('{object} has been deleted.', domain='ohmyadmin'))

            redirect_to = self.generate_url(request)
            if 'hx-request' in request.headers:
                return ActionResponse().redirect(request, redirect_to)
            return RedirectResponse(redirect_to, 302)

        cancel_url = self.generate_url(request)
        return self.render_to_response(
            request,
            'ohmyadmin/resources/delete.html',
            {
                'page_title': _('Delete {object}', domain='ohmyadmin').format(object=model),
                'object': model,
                'cancel_url': cancel_url,
            },
        )

    def get_routes(self) -> list[BaseRoute]:
        return [
            Route(
                '/',
                self.index_view,
                name=f'{self.get_path_name()}.index',
                methods=['get', 'post', 'put', 'patch', 'delete'],
            ),
            Route('/new', self.create_view, name=f'{self.get_path_name()}.create', methods=['get', 'post']),
            Route('/{pk}/edit', self.update_view, name=f'{self.get_path_name()}.edit', methods=['get', 'post']),
            Route(
                '/{pk}/delete',
                self.delete_view,
                name=f'{self.get_path_name()}.delete',
                methods=['get', 'post', 'delete'],
            ),
        ]

    def as_route(self) -> Mount:
        return Mount(f'/resources/{self.slug}', self)

    def page_url(self, request: Request, method: str, **path_params: typing.Any) -> str:
        return request.url_for(f'{self.get_path_name()}.{method}', **path_params)

    def redirect_to_action(self, request: Request, action: str, pk: typing.Any | None = None) -> RedirectResponse:
        path_params: dict[str, typing.Any] = {}
        if pk:
            path_params['pk'] = pk
        return self.redirect_to_path(request, f'{self.get_path_name()}.{action}', **path_params)

    @classmethod
    def generate_url(cls, request: Request) -> str:
        return request.url_for(f'{cls.get_path_name()}.index')

    @classmethod
    def get_path_name(cls) -> str:
        return f'ohmyadmin.resources.{cls.slug}'

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope['state']['page'] = self
        return await super().__call__(scope, receive, send)
