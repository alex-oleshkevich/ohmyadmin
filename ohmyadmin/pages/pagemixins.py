import json
import typing
from starlette.requests import Request
from starlette.responses import Response
from starlette_babel import gettext_lazy as _
from unittest import mock

from ohmyadmin import actions
from ohmyadmin.datasource.base import DataSource
from ohmyadmin.filters import BaseFilter, UnboundFilter
from ohmyadmin.ordering import get_ordering_value
from ohmyadmin.pagination import Pagination, get_page_size_value, get_page_value
from ohmyadmin.views.base import IndexView
from ohmyadmin.views.table import TableColumn, TableView


def get_search_value(request: Request, param_name: str) -> str:
    return request.query_params.get(param_name, '').strip()


class HasPageActions:
    page_actions: typing.Sequence[actions.PageAction] | None = None

    def get_page_actions(self, _: Request) -> list[actions.PageAction]:
        return list(self.page_actions or [])

    async def dispatch_action(self, request: Request, action_slug: str) -> Response:
        actions_ = {
            action.slug: action for action in self.get_page_actions(request) if isinstance(action, actions.Dispatch)
        }

        try:
            action = actions_[action_slug]
        except KeyError:
            raise ValueError(f'Action "{action_slug}" is not defined.')

        return await action.dispatch(request)

    async def handler(self, request: Request) -> Response:
        if '_action' in request.query_params:
            return await self.dispatch_action(request, request.query_params['_action'])

        return await super().handler(request)


class HasObjectActions:
    object_actions: typing.Sequence[actions.ObjectAction] | None = None

    def get_object_actions(self, request: Request, obj: typing.Any) -> list[actions.ObjectAction]:
        return list(self.object_actions or [])

    async def dispatch_object_action(self, request: Request, action_slug: str) -> Response:
        actions_ = {
            action.slug: action
            for action in self.get_object_actions(request, mock.MagicMock()) or []
            if isinstance(action, actions.Dispatch)
        }

        try:
            action = actions_[action_slug]
        except KeyError:
            raise ValueError(f'Object action "{action_slug}" is not defined.')

        return await action.dispatch(request)

    async def handler(self, request: Request) -> Response:
        if '_object_action' in request.query_params:
            return await self.dispatch_object_action(request, request.query_params['_object_action'])

        return await super().handler(request)


class HasBatchActions:
    batch_actions: typing.Sequence[actions.BatchAction] | None = None

    def get_batch_actions(self, request: Request) -> list[actions.BatchAction]:
        return list(self.batch_actions or [])

    async def dispatch_batch_action(self, request: Request, action_slug: str) -> Response:
        actions_ = {action.slug: action for action in self.get_batch_actions(request)}
        try:
            action = actions_[action_slug]
        except KeyError:
            raise ValueError(f'Batch action "{action_slug}" is not defined.')

        return await action.dispatch(request)

    async def handler(self, request: Request) -> Response:
        if '_batch_action' in request.query_params:
            return await self.dispatch_batch_action(request, request.query_params['_batch_action'])

        return await super().handler(request)


class HasFilters:
    filters: typing.Sequence[UnboundFilter] | None = None

    def get_filters(self, request: Request) -> typing.Sequence[UnboundFilter]:
        return self.filters or []

    async def create_filters(self, request: Request) -> list[BaseFilter]:
        return [await _filter.create(request) for _filter in self.get_filters(request)]


class IndexViewMixin(HasPageActions, HasFilters, HasObjectActions, HasBatchActions):
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

    def get_sortable_fields(self, request: Request) -> list[str]:
        return [column.sort_by for column in self.get_table_columns(request) if column.sortable]

    def get_searchable_fields(self, request: Request) -> list[str]:
        return [column.search_in for column in self.get_table_columns(request) if column.searchable]

    def is_searchable(self, request: Request) -> bool:
        return bool(self.get_searchable_fields(request))

    def get_search_placeholder(self, request: Request) -> str:
        template = _('Search in {fields}.')
        fields = ', '.join([str(column.label) for column in self.get_table_columns(request) if column.searchable])
        return template.format(fields=fields)

    def get_table_columns(self, request: Request) -> typing.Sequence[TableColumn]:
        return self.columns or []

    async def get_objects(self, request: Request, filters: list[BaseFilter]) -> Pagination:
        page_number = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, self.max_page_size, self.page_size)
        search_term = get_search_value(request, self.search_param)
        ordering = get_ordering_value(request, self.ordering_param)

        query = self.datasource.get_for_index()
        if search_term:
            query = query.apply_search(search_term, self.get_searchable_fields(request))

        if ordering:
            query = query.apply_ordering(ordering, self.get_sortable_fields(request))

        for _filter in filters:
            query = _filter.apply(request, query)

        return await query.paginate(request, page=page_number, page_size=page_size)

    def get_view(self, request: Request) -> IndexView:
        return TableView(columns=self.get_table_columns(request))

    async def dispatch_index_view(self, request: Request) -> Response:
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
