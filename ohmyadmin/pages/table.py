import typing
from starlette.requests import Request
from starlette.responses import Response
from starlette_babel import gettext_lazy as _

from ohmyadmin.datasource.base import DataSource
from ohmyadmin.ordering import get_ordering_value
from ohmyadmin.pages.base import Page
from ohmyadmin.pagination import get_page_size_value, get_page_value
from ohmyadmin.resources import get_search_value
from ohmyadmin.views.table import TableColumn, TableView


class TablePage(Page):
    __abstract__ = True
    datasource: typing.ClassVar[DataSource]
    page_param: typing.ClassVar[str] = 'page'
    page_size_param: typing.ClassVar[str] = 'page_size'
    search_param: typing.ClassVar[str] = 'search'
    ordering_param: typing.ClassVar[str] = 'ordering'
    page_size: typing.ClassVar[int] = 25
    max_page_size: typing.ClassVar[int] = 100
    columns: typing.ClassVar[typing.Sequence[TableColumn] | None] = None

    def __init__(self) -> None:
        self._columns = self.columns or []

    @property
    def sortable_fields(self) -> list[str]:
        return [column.sort_by for column in self.columns if column.sortable]

    @property
    def searchable_fields(self) -> list[str]:
        return [column.search_in for column in self.columns if column.searchable]

    @property
    def searchable(self) -> bool:
        return bool(self.searchable_fields)

    @property
    def search_placeholder(self) -> str:
        template = _('Search in {fields}.')
        fields = ', '.join([str(column.label) for column in self.columns if column.searchable])
        return template.format(fields=fields)

    async def get_objects(self, request: Request) -> Page:
        page_number = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, self.max_page_size, self.page_size)
        search_term = get_search_value(request, self.search_param)
        ordering = get_ordering_value(request, self.ordering_param)

        query = self.datasource.get_for_index()
        if search_term:
            query = query.apply_search(search_term, self.searchable_fields)
        if ordering:
            query = query.apply_ordering(ordering, self.sortable_fields)
        return await query.paginate(request, page=page_number, page_size=page_size)

    async def get(self, request: Request) -> Response:
        objects = await self.get_objects(request)
        view = TableView(columns=self._columns)
        view_content = view.render(request, objects)

        if 'hx-request' in request.headers:
            return self.render_to_response(
                request,
                'ohmyadmin/pages/table/_content.html',
                {
                    'request': request,
                    'view_content': view_content,
                    'objects': objects,
                },
                headers={'hx-push-url': str(request.url)},
            )

        return self.render_to_response(
            request,
            'ohmyadmin/pages/table/table.html',
            {
                'page': self,
                'objects': objects,
                'view_content': view_content,
                'page_title': self.label_plural,
                'search_term': get_search_value(request, self.search_param),
            },
        )
