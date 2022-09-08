from __future__ import annotations

import abc
import itertools
import sqlalchemy as sa
import typing
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import URL, FormData, MultiDict
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import Receive, Scope, Send
from urllib.parse import parse_qsl, urlencode

from ohmyadmin.actions import Action
from ohmyadmin.helpers import render_to_string
from ohmyadmin.i18n import _
from ohmyadmin.pagination import Page

Formatter = typing.Callable[[typing.Any], str]


class Column:
    name: str
    label: str
    sortable: bool = False
    searchable: bool = False

    def __init__(
        self,
        name: str,
        *,
        label: str = '',
        sortable: bool = False,
        searchable: bool = False,
        source: str = '',
        value_format: str | Formatter | None = None,
        sort_by: str = '',
        search_in: list[str] | None = None,
        link_factory: typing.Callable[[Request, typing.Any], str] | None = None,
    ) -> None:
        self.name = name
        self.label = label or name.replace('_', ' ').title()
        self.sortable = sortable
        self.searchable = searchable
        self.source = source or name
        self.value_format = value_format
        self.sort_by = sort_by or self.source
        self.search_in = search_in or [self.source]
        self.link_factory = link_factory

    def get_value(self, obj: typing.Any) -> typing.Any:
        parts = self.source.split('.')
        value = obj
        for part in parts:
            value = getattr(value, part)
        return value

    def format_value(self, value: typing.Any) -> str:
        if callable(self.value_format):
            return self.value_format(value)
        if self.value_format:
            return self.value_format % value
        return value

    def get_display_value(self, obj: typing.Any) -> str:
        return self.format_value(self.get_value(obj))


class ActionGroup(Action):
    def __init__(self, children: list[Action]) -> None:
        self.children = children

    def render(self) -> str:
        return render_to_string('ohmyadmin/ui/action_group.html', {'action': self})

    def __iter__(self) -> typing.Iterator[Action]:
        return iter(self.children)


class BatchAction(abc.ABC):
    id: str
    label: str = 'Unlabelled'
    confirmation: str = ''
    dangerous: bool = False

    @abc.abstractmethod
    async def apply(self, request: Request, ids: list[str], params: dict[str, str]) -> Response:
        ...


def get_ordering_value(request: Request, param_name: str) -> list[str]:
    return request.query_params.getlist(param_name)


def get_search_value(request: Request, param_name: str) -> str:
    return request.query_params.get(param_name, '')


def get_page_value(request: Request, param_name: str) -> int:
    page = 1
    try:
        page = max(1, int(request.query_params.get(param_name, 1)))
    except (TypeError, ValueError):
        pass
    return page


def get_page_size_value(request: Request, param_name: str, allowed: list[int], default: int) -> int:
    page_size = default
    try:
        page_size = int(request.query_params.get(param_name, default))
    except (TypeError, ValueError):
        pass
    if page_size not in allowed:
        page_size = default
    return page_size


class BaseFilter(abc.ABC):
    @abc.abstractmethod
    def apply(self, request: Request, queryset: sa.sql.Select) -> sa.sql.Select:
        ...


class OrderingFilter(BaseFilter):
    def __init__(self, columns: list[str], query_param: str) -> None:
        self.columns = columns
        self.query_param = query_param

    def apply(self, request: Request, queryset: sa.sql.Select) -> sa.sql.Select:
        ordering = get_ordering_value(request, self.query_param)
        if ordering:
            queryset = queryset.order_by(None)
        for order in ordering:
            field_name = order.lstrip('-')
            if field_name not in self.columns:
                continue

            queryset = queryset.order_by(sa.desc(field_name) if order.startswith('-') else field_name)
        return queryset


class SearchFilter(BaseFilter):
    def __init__(self, columns: list[str], query_param: str) -> None:
        self.columns = columns
        self.query_params = query_param

    def apply(self, request: Request, queryset: sa.sql.Select) -> sa.sql.Select:
        clauses = []
        search_query = get_search_value(request, self.query_params)
        if not search_query:
            return queryset

        for field in self.columns:
            search_token = f'%{search_query.lower()}%'
            clauses.append(sa.column(field).ilike(search_token))

        if clauses:
            queryset = queryset.where(sa.or_(*clauses))

        return queryset


SortingType = typing.Literal['asc', 'desc']


class SortingHelper:
    def __init__(self, query_param_name: str) -> None:
        self.query_param_name = query_param_name

    def get_current_ordering(self, request: Request, sort_field: str) -> SortingType | None:
        ordering = get_ordering_value(request, self.query_param_name)
        for order in ordering:
            if order == sort_field:
                return 'asc'
            if order == f'-{sort_field}':
                return 'desc'

        return None

    def get_current_ordering_index(self, request: Request, sort_field: str) -> int | None:
        for index, param_name in enumerate(get_ordering_value(request, self.query_param_name)):
            if param_name.endswith(sort_field):
                return index + 1
        return None

    def get_next_sorting(self, current_sorting: SortingType | None) -> SortingType | None:
        match current_sorting:
            case None:
                return 'asc'
            case 'asc':
                return 'desc'
            case 'desc':
                return None

    def get_url(self, request: Request, sort_field: str) -> URL:
        ordering = get_ordering_value(request, self.query_param_name).copy()
        if sort_field in ordering:
            index = ordering.index(sort_field)
            ordering[index] = f'-{sort_field}'
        elif f'-{sort_field}' in ordering:
            ordering.remove(f'-{sort_field}')
        else:
            ordering.append(sort_field)

        params = MultiDict(parse_qsl(request.url.query, keep_blank_values=True))
        params.setlist(self.query_param_name, ordering)
        url = request.url.replace(query=urlencode(params.multi_items()))
        return url

    def should_show_index(self, request: Request) -> bool:
        return len(get_ordering_value(request, self.query_param_name)) > 1


class TableView:
    label: str = 'Untitled'
    columns: list[Column] = []
    page: int = 1
    page_param: str = 'page'
    page_size: int = 20
    page_sizes: list[int] = [25, 50, 75, 100]
    page_size_param: str = 'page_size'
    search_param: str = 'search'
    ordering_param: str = 'ordering'
    queryset: sa.sql.Select | None = None
    search_placeholder: str = _('Search...')

    def __init__(self, dbsession: sessionmaker) -> None:
        self.dbsession = dbsession

    def get_queryset(self, request: Request) -> sa.sql.Select:
        assert self.queryset is not None, 'Queryset is not defined.'
        return self.queryset

    def get_filters(self) -> typing.Iterable[BaseFilter]:
        filters: list[BaseFilter] = []

        # attach ordering filter
        if sortables := [column.sort_by for column in self.columns if column.sortable]:
            filters.append(OrderingFilter(sortables, self.ordering_param))

        # make search filter
        if searchables := list(itertools.chain.from_iterable([c.search_in for c in self.columns if c.searchable])):
            filters.append(SearchFilter(columns=searchables, query_param=self.search_param))

        return filters

    def apply_filters(self, request: Request, stmt: sa.sql.Select) -> sa.sql.Select:
        for filter in self.get_filters():
            stmt = filter.apply(request, stmt)
        return stmt

    async def get_object_count(self, session: AsyncSession, queryset: sa.sql.Select) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(queryset)
        result = await session.scalars(stmt)
        return result.one()

    async def get_objects(self, session: AsyncSession, queryset: sa.sql.Select) -> typing.Iterable:
        result = await session.scalars(queryset)
        return result.all()

    async def paginate_queryset(self, request: Request, queryset: sa.sql.Select) -> Page:
        page_number = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, self.page_sizes, self.page_size)
        offset = (page_number - 1) * page_size

        row_count = await self.get_object_count(request.state.dbsession, queryset)
        queryset = queryset.limit(page_size).offset(offset)
        rows = await self.get_objects(request.state.dbsession, queryset)
        return Page(rows=list(rows), total_rows=row_count, page=page_number, page_size=page_size)

    def row_actions(self, request: Request, entity: object) -> typing.Iterable[Action]:
        return []

    def batch_actions(self, request: Request) -> typing.Iterable[BatchAction]:
        return []

    def table_actions(self, request: Request) -> typing.Iterable[Action]:
        return []

    async def _dispatch_batch_action(self, request: Request, action_name: str, body: FormData) -> Response:
        for action in self.batch_actions(request):
            if action.id == action_name:
                ids = body.getlist('selected')
                return await action.apply(request, ids, body)
        raise RuntimeError('Unknown batch action: ' + action_name)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with self.dbsession() as session:
            request = Request(scope, receive, send)
            request.state.dbsession = session

            if request.method == 'POST':
                data = await request.form()
                match data:
                    case {'_batch': action_name}:
                        response = await self._dispatch_batch_action(request, action_name, data)
                    case _:
                        response = RedirectResponse(request.headers.get('referrer'))
            else:
                queryset = self.get_queryset(request)
                queryset = self.apply_filters(request, queryset)
                objects = await self.paginate_queryset(request, queryset)

                response = request.state.admin.render_to_response(
                    request,
                    'ohmyadmin/table.html',
                    {
                        'table': self,
                        'objects': objects,
                        'page_title': self.label,
                        'sorting_helper': SortingHelper(self.ordering_param),
                        'search_query': get_search_value(request, self.search_param),
                    },
                )
            await response(scope, receive, send)
