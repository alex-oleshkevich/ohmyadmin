import json
import typing
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route
from starlette_babel import gettext_lazy as _

from ohmyadmin.datasource.base import DataSource
from ohmyadmin.filters import BaseFilter
from ohmyadmin.ordering import get_ordering_value
from ohmyadmin.pages.page import Page
from ohmyadmin.pages.pagemixins import HasBatchActions, HasFilters, HasObjectActions, HasPageActions
from ohmyadmin.pagination import Pagination, get_page_size_value, get_page_value
from ohmyadmin.views.base import IndexView
from ohmyadmin.views.table import TableColumn, TableView


def get_search_value(request: Request, param_name: str) -> str:
    return request.query_params.get(param_name, '').strip()


class TablePage(HasPageActions, HasFilters, HasObjectActions, HasBatchActions, Page):
    __abstract__ = True
    datasource: typing.ClassVar[DataSource]
    page_param: typing.ClassVar[str] = 'page'
    page_size_param: typing.ClassVar[str] = 'page_size'
    search_param: typing.ClassVar[str] = 'search'
    ordering_param: typing.ClassVar[str] = 'ordering'
    page_size: typing.ClassVar[int] = 25
    max_page_size: typing.ClassVar[int] = 100
    columns: typing.Sequence[TableColumn] | None = None

    def __init__(self) -> None:
        self.columns = self.columns or []

    @property
    def sortable_fields(self) -> list[str]:
        return [column.sort_by for column in self.get_columns() if column.sortable]

    @property
    def searchable_fields(self) -> list[str]:
        return [column.search_in for column in self.get_columns() if column.searchable]

    @property
    def searchable(self) -> bool:
        return bool(self.searchable_fields)

    @property
    def search_placeholder(self) -> str:
        template = _('Search in {fields}.')
        fields = ', '.join([str(column.label) for column in self.get_columns() if column.searchable])
        return template.format(fields=fields)

    def get_columns(self) -> typing.Sequence[TableColumn]:
        return self.columns or []

    async def get_objects(self, request: Request, filters: list[BaseFilter]) -> Pagination:
        page_number = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, self.max_page_size, self.page_size)
        search_term = get_search_value(request, self.search_param)
        ordering = get_ordering_value(request, self.ordering_param)

        query = self.datasource.get_for_index()
        if search_term:
            query = query.apply_search(search_term, self.searchable_fields)

        if ordering:
            query = query.apply_ordering(ordering, self.sortable_fields)

        for _filter in filters:
            query = _filter.apply(request, query)

        return await query.paginate(request, page=page_number, page_size=page_size)

    def get_view(self, request: Request) -> IndexView:
        return TableView(columns=self.get_columns())

    async def get(self, request: Request) -> Response:
        filters = await self.create_filters(request)
        objects = await self.get_objects(request, filters)
        view = self.get_view(request)
        view_content = view.render(request, objects)

        if request.headers.get('hx-target', '') == 'filter-bar':
            headers = {}
            if 'clear' in request.query_params:
                headers = {
                    'hx-push-url': str(request.url.remove_query_params('clear')),
                    'hx-trigger-after-settle': json.dumps({'refresh-datatable': ''}),
                }
            return self.render_to_response(
                request,
                'ohmyadmin/pages/table/_filters.html',
                {'filters': filters},
                headers=headers,
            )

        if request.headers.get('hx-target', '') == 'data':
            return self.render_to_response(
                request,
                'ohmyadmin/pages/table/_content.html',
                {
                    'request': request,
                    'objects': objects,
                    'view_content': view_content,
                },
                headers={
                    'hx-push-url': str(request.url),
                    'hx-trigger-after-settle': json.dumps({'filters-reload': ''}),
                },
            )

        active_filter_count = sum([1 for filter in filters if filter.is_active(request)])
        return self.render_to_response(
            request,
            'ohmyadmin/pages/table/table.html',
            {
                'page': self,
                'objects': objects,
                'filters': filters,
                'view_content': view_content,
                'page_title': self.label_plural,
                'active_filter_count': active_filter_count,
                'search_term': get_search_value(request, self.search_param),
            },
        )

    async def handler(self, request: Request) -> Response:
        request.state.datasource = self.datasource
        return await super().handler(request)

    def as_route(self) -> BaseRoute:
        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        return Route(f'/{self.slug}', self, methods=methods, name=self.get_path_name())
