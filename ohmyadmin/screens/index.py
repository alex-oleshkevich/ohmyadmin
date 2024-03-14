import typing

from starlette.requests import Request
from starlette.responses import Response
from starlette_babel import gettext_lazy as _

from ohmyadmin import htmx
from ohmyadmin.actions.actions import Action, ModalAction
from ohmyadmin.components.index import IndexView
from ohmyadmin.datasources.datasource import DataSource
from ohmyadmin.filters import Filter, OrderingFilter, SearchFilter
from ohmyadmin.pagination import get_page_size_value, get_page_value
from ohmyadmin.templating import render_to_response
from ohmyadmin.screens.base import Screen


class IndexScreen(Screen):
    datasource: typing.ClassVar[DataSource | None] = None

    page_param: typing.ClassVar[str] = "page"
    page_size_param: typing.ClassVar[str] = "page_size"
    page_size: typing.ClassVar[int] = 25
    page_sizes: typing.ClassVar[typing.Sequence[int]] = [10, 25, 50, 100]

    filters: typing.Sequence[Filter] = tuple()
    batch_actions: typing.Sequence[ModalAction] = tuple()

    search_param: str = "search"
    search_placeholder: str = _("Start typing to search...")
    searchable_fields: typing.Sequence[str] = tuple()
    search_filter: Filter | None = None

    # ordering: typing.Sequence[str] = tuple()
    ordering_param: typing.ClassVar[str] = "ordering"
    ordering_fields: typing.Sequence[str] = tuple()
    ordering_filter: Filter | None = None

    view_class: IndexView = IndexView
    template: str = "ohmyadmin/screens/index/page.html"
    content_template: str = "ohmyadmin/screens/index/content.html"

    def __init__(self) -> None:
        if self.search_filter is None:
            self.search_filter = SearchFilter(model_fields=self.searchable_fields, field_name=self.search_param)

        if self.ordering_filter is None:
            self.ordering_filter = OrderingFilter(model_fields=self.ordering_fields, field_name=self.ordering_param)

    @property
    def searchable(self) -> bool:
        # FIXME: we need a protocol here so custom search filters can report if they are searchable or not
        if isinstance(self.search_filter, SearchFilter):
            return bool(self.search_filter.model_fields)
        return bool(self.searchable_fields)

    def get_query(self, request: Request) -> DataSource:
        assert self.datasource, "No data source configured."
        return self.datasource.get_query_for_list()

    def get_ordering_param(self) -> str:
        return self.ordering_param

    def get_batch_actions(self) -> typing.Sequence[ModalAction]:
        return self.batch_actions

    def get_ordering_fields(self) -> typing.Sequence[str]:
        return self.ordering_fields

    async def apply_filters(self, request: Request, query: DataSource) -> DataSource:
        filters = [self.search_filter, self.ordering_filter, *self.filters]

        for filter_ in filters:
            filter_form = await filter_.get_form(request)
            query = filter_.apply(request, query, filter_form)
        return query

    def render_content(self, request: Request, context: typing.Mapping[str, typing.Any]) -> Response:
        return render_to_response(request, self.content_template, context)

    def render_page(self, request: Request, context: typing.Mapping[str, typing.Any]) -> Response:
        return render_to_response(request, self.template, context)

    async def dispatch(self, request: Request) -> Response:
        page = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, max(self.page_sizes), self.page_size)
        query = self.get_query(request)
        query = await self.apply_filters(request, query)
        models = await query.paginate(request, page, page_size)
        should_refresh_filters = htmx.matches_target(request, "datatable") and any(
            ["x-ohmyadmin-force-filter-refresh" in request.headers, any([f.is_active(request) for f in self.filters])]
        )

        component = self.view_class(models)
        if htmx.matches_target(request, "datatable"):
            return self.render_content(
                request,
                {
                    "request": request,
                    "component": component,
                    "screen": self,
                    "models": models,
                    "oob_filters": should_refresh_filters,
                },
            )

        # clean url from unused filters
        push_url = request.url
        for filter_ in self.filters:
            if not filter_.is_active(request):
                push_url = push_url.remove_query_params([f.name for f in filter_.form])
        if not request.query_params.get(self.search_param):
            push_url = push_url.remove_query_params(self.search_param)
        setattr(request, "_url", push_url)  # TODO: fixme

        response = self.render_page(
            request,
            {
                "screen": self,
                "models": models,
                "request": request,
                "component": component,
                "page_title": self.label,
                "page_description": self.description,
                "oob_filters": should_refresh_filters,
                "search_term": request.query_params.get(self.search_param, ""),
            },
        )
        return htmx.push_url(response, push_url)

    def get_action_handlers(self) -> typing.Sequence[Action]:
        return [
            *self.batch_actions,
        ]
