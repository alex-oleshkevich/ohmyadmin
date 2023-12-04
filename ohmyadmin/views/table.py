import dataclasses
import functools
import typing

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route
from starlette_babel import gettext_lazy as _

from ohmyadmin import htmx
from ohmyadmin.actions.actions import Action, CallbackAction
from ohmyadmin.datasources.datasource import DataSource
from ohmyadmin.filters import Filter, OrderingFilter, SearchFilter
from ohmyadmin.formatters import CellFormatter, StringFormatter
from ohmyadmin.helpers import snake_to_sentence
from ohmyadmin.ordering import SortingHelper
from ohmyadmin.pagination import get_page_size_value, get_page_value
from ohmyadmin.templating import render_to_response
from ohmyadmin.views.base import View


def default_value_getter(obj: typing.Any, attr: str) -> typing.Any:
    return getattr(obj, attr, 'undefined!')


class Column:
    def __init__(
        self,
        name: str,
        label: str | None = None,
        searchable: bool = False,
        sortable: bool = False,
        search_in: str | None = None,
        sort_by: str | None = None,
        formatter: CellFormatter = StringFormatter(),
        value_getter: typing.Callable[[typing.Any], typing.Any] | None = None,
    ) -> None:
        self.name = name
        self.searchable = searchable
        self.sortable = sortable
        self.search_in = search_in or name
        self.sort_by = sort_by or name
        self.formatter = formatter
        self.label = label or snake_to_sentence(name)
        self.value_getter = value_getter or functools.partial(default_value_getter, attr=name)

    def get_value(self, obj: typing.Any) -> typing.Any:
        return self.value_getter(obj)

    def format_value(self, request: Request, value: typing.Any) -> str:
        return self.formatter(request, value)


class TableView(View):
    page_param: str = 'page'
    page_size_param: str = 'page_size'
    page_size: int = 50
    page_sizes: list[int] = [10, 25, 50, 100]
    ordering_param: str = 'ordering'
    template = 'ohmyadmin/views/table/page.html'
    datasource: DataSource | None = None
    columns: list[Column] | None = None
    filters: list[Filter] | None = None
    actions: list[Action] | None = None

    search_param: str = 'search'
    search_placeholder: str = ''

    def __init__(self) -> None:
        self.columns = self.columns or []
        self.filters = self.filters or []
        self.actions = self.actions or []
        self.filters.extend([
            OrderingFilter(self.ordering_param, [column.sort_by for column in self.columns if column.sortable]),
            SearchFilter(self.search_param, [column.search_in for column in self.columns if column.searchable])
        ])
        self.search_placeholder = self.search_placeholder or _('Search in {fields}...').format(fields=', '.join([
            column.label for column in self.columns if column.searchable
        ]))

    async def dispatch(self, request: Request) -> Response:
        page = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, max(self.page_sizes), self.page_size)
        sorting = SortingHelper(request, self.ordering_param)

        query = self.datasource.get_query_for_list()
        for _filter in self.filters:
            query = _filter.apply(request, query)

        rows = await query.paginate(request, page, page_size)
        template = self.template
        if htmx.matches_target(request, 'datatable'):
            template = 'ohmyadmin/views/table/table.html'

        response = render_to_response(request, template, {
            'page_title': self.label,
            'page_description': self.description,
            'objects': rows,
            'table': self,
            'sorting': sorting,
            'search_term': request.query_params.get(self.search_param, ''),
        })
        return htmx.push_url(response, str(request.url))

    def get_route(self) -> BaseRoute:
        action_routes = [
            Route(
                '/actions/' + action.slug, action,
                name=self.url_name + '.action.' + action.slug,
                methods=['get', 'post', 'delete', 'patch', 'put']
            )
            for action in self.actions if isinstance(action, CallbackAction)
        ]
        return Mount('/' + self.slug, routes=[
            Route('/', self.dispatch, name=self.url_name),
            *action_routes,
        ])


@dataclasses.dataclass
class _CallbackActionWrapper:
    table: TableView
    action: CallbackAction

    @property
    def url_name(self) -> str:
        return self.table.url_name + '.action.' + self.action.slug
