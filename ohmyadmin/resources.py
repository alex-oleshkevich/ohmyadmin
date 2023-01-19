import functools
import typing
import wtforms
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette_babel import gettext_lazy as _
from starlette_flash import flash

from ohmyadmin import actions
from ohmyadmin.actions import BatchDelete, DeleteObjectAction
from ohmyadmin.datasource.base import DataSource
from ohmyadmin.forms import create_form
from ohmyadmin.helpers import LazyURL
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

    def get_table_columns(self) -> typing.Sequence[TableColumn]:
        return self.columns or []

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
            columns = self.get_table_columns()

            get_filters = self.get_filters
            get_page_actions = self.get_page_actions
            get_object_actions = self.get_object_actions
            get_batch_actions = self.get_batch_actions

        return IndexPage

    async def index_view(self, request: Request) -> Response:
        page_class = self.get_index_page_class(request)
        page_instance = page_class()
        return await page_instance.handler(request)

    async def edit_view(self, request: Request) -> Response:
        pk = request.path_params.get('pk')
        if request.method == 'POST':
            flash(request).success('Submitted')
            return self.redirect_to_action(request, 'edit' if pk else 'create', pk=pk)

        context = {'resource': self, 'page_url': functools.partial(self.page_url, request)}
        if pk:
            return self.render_to_response(request, 'ohmyadmin/resources/edit.html', context)
        return self.render_to_response(request, 'ohmyadmin/resources/create.html', context)

    async def delete_view(self, request: Request) -> Response:
        request.path_params.get('pk')
        if request.method == 'POST':
            flash(request).success('Submitted')
            return self.redirect_to_action(request, 'index')

        context = {'page_url': functools.partial(self.page_url, request)}
        return self.render_to_response(request, 'ohmyadmin/resources/delete.html', context)

    def get_routes(self) -> list[BaseRoute]:
        return [
            Route(
                '/',
                self.index_view,
                name=f'{self.get_path_name()}.index',
                methods=['get', 'post', 'put', 'patch', 'delete'],
            ),
            Route('/new', self.edit_view, name=f'{self.get_path_name()}.create', methods=['get', 'post']),
            Route('/{pk}/edit', self.edit_view, name=f'{self.get_path_name()}.edit', methods=['get', 'post']),
            Route('/{pk}/delete', self.delete_view, name=f'{self.get_path_name()}.delete', methods=['get', 'post']),
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
