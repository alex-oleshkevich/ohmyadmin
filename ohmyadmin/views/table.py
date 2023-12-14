import functools
import typing

from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route
from starlette_babel import gettext_lazy as _

from ohmyadmin import htmx
from ohmyadmin.actions.actions import Action, WithRoute
from ohmyadmin.actions.object_actions import FormAction, ObjectAction
from ohmyadmin.datasources.datasource import DataSource
from ohmyadmin.filters import Filter, OrderingFilter, SearchFilter
from ohmyadmin.formatters import CellFormatter, StringFormatter
from ohmyadmin.helpers import snake_to_sentence
from ohmyadmin.ordering import SortingHelper
from ohmyadmin.pagination import get_page_size_value, get_page_value
from ohmyadmin.templating import render_to_response
from ohmyadmin.views.base import ExposeViewMiddleware, View


def default_value_getter(obj: typing.Any, attr: str) -> typing.Any:
    return getattr(obj, attr, "undefined!")


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
    page_param: typing.ClassVar[str] = "page"
    page_size_param: typing.ClassVar[str] = "page_size"
    page_size: typing.ClassVar[int] = 50
    page_sizes: typing.ClassVar[typing.Sequence[int]] = [10, 25, 50, 100]
    ordering_param: typing.ClassVar[str] = "ordering"
    template = "ohmyadmin/views/table/page.html"
    datasource: typing.ClassVar[DataSource | None] = None
    columns: typing.Sequence[Column] = tuple()
    filters: typing.Sequence[Filter] = tuple()
    actions: typing.Sequence[Action] = tuple()
    row_actions: typing.Sequence[ObjectAction] = tuple()
    batch_actions: typing.Sequence[FormAction] = tuple()

    search_param: str = "search"
    search_placeholder: str = ""

    def __init__(self) -> None:
        self.columns = list(self.columns)
        self.actions = list(self.actions)
        self.row_actions = list(self.row_actions)
        self.batch_actions = list(self.batch_actions)
        self.filters: list[Filter] = list(self.filters)
        self.filters.extend(
            [
                OrderingFilter(self.ordering_param, [column.sort_by for column in self.columns if column.sortable]),
                SearchFilter(self.search_param, [column.search_in for column in self.columns if column.searchable]),
            ]
        )
        self.search_placeholder = self.search_placeholder or _("Search in {fields}...", domain="ohmyadmin").format(
            fields=", ".join([column.label for column in self.columns if column.searchable])
        )

    @property
    def searchable(self) -> bool:
        return any([column.searchable for column in self.columns])

    def get_query(self, request: Request) -> DataSource:
        assert self.datasource, "No data source configured."
        return self.datasource.get_query_for_list()

    async def apply_filters(self, request: Request, query: DataSource) -> DataSource:
        for filter_ in self.filters:
            filter_form = await filter_.get_form(request)
            query = filter_.apply(request, query, filter_form)
        return query

    async def dispatch(self, request: Request) -> Response:
        page = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, max(self.page_sizes), self.page_size)
        sorting = SortingHelper(request, self.ordering_param)

        query = self.get_query(request)
        query = await self.apply_filters(request, query)

        rows = await query.paginate(request, page, page_size)
        template = self.template
        if htmx.matches_target(request, "datatable"):
            template = "ohmyadmin/views/table/table.html"

        if htmx.matches_target(request, "view-filters"):
            template = "ohmyadmin/views/table/filters_bar.html"

        response = render_to_response(
            request,
            template,
            {
                "table": self,
                "objects": rows,
                "sorting": sorting,
                "page_title": self.label,
                "page_description": self.description,
                "oob_filters": "x-ohmyadmin-force-filter-refresh" in request.headers,
                "search_term": request.query_params.get(self.search_param, ""),
            },
        )
        return response

    def get_route(self) -> BaseRoute:
        return Mount(
            "/" + self.slug,
            routes=[
                Route("/", self.dispatch, name=self.url_name),
                Mount(
                    "/actions",
                    routes=[
                        action.get_route(self.url_name) for action in self.actions if isinstance(action, WithRoute)
                    ],
                    middleware=[
                        Middleware(ExposeViewMiddleware, view=self),
                    ],
                ),
                Mount(
                    "/object-actions",
                    routes=[
                        action.get_route(self.url_name)
                        for action in [*self.row_actions, *self.batch_actions]
                        if isinstance(action, WithRoute)
                    ],
                    middleware=[
                        Middleware(ExposeViewMiddleware, view=self),
                    ],
                ),
            ],
        )
