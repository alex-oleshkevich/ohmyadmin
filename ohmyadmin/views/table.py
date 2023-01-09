import typing
from markupsafe import Markup
from starlette.requests import Request

from ohmyadmin.formatters import DataFormatter, ToStringFormatter
from ohmyadmin.ordering import SortingHelper
from ohmyadmin.pagination import Pagination
from ohmyadmin.shortcuts import render_to_string
from ohmyadmin.views.base import IndexView


class TableColumn:
    def __init__(
        self,
        name: str,
        label: str | None = None,
        searchable: bool = False,
        sortable: bool = False,
        formatter: DataFormatter | None = None,
        search_in: str | None = None,
        sort_by: str | None = None,
    ) -> None:
        self.name = name
        self.sortable = sortable
        self.searchable = searchable
        self.search_in = search_in or name
        self.sort_by = sort_by or name
        self.formatter = formatter or ToStringFormatter()
        self.label = label or name.title().replace('_', ' ')

    def get_value(self, obj: typing.Any) -> typing.Any:
        return getattr(obj, self.name, 'undefined')

    def format_value(self, request: Request, value: typing.Any) -> str:
        return self.formatter(request, value)

    def render(self, request: Request, obj: typing.Any) -> str:
        value = self.get_value(obj)
        display_value = self.format_value(request, value)
        return request.state.admin.render_to_string(
            request,
            'ohmyadmin/views/table/table_cell.html',
            {
                'column': self,
                'value': display_value,
            },
        )

    def render_head_cell(self, request: Request) -> str:
        sorting: SortingHelper = request.state.table_sorting
        return request.state.admin.render_to_string(
            request,
            'ohmyadmin/views/table/table_head_cell.html',
            {
                'column': self,
                'sorting': sorting,
            },
        )


class TableView(IndexView):
    def __init__(self, columns: typing.Sequence[TableColumn], query_param: str = 'ordering') -> None:
        self.columns = columns
        self.query_param = query_param

    def render(self, request: Request, objects: Pagination[typing.Any]) -> str:
        request.state.table_sorting = SortingHelper(request, self.query_param)
        return Markup(
            render_to_string(
                request,
                'ohmyadmin/views/table/table.html',
                {
                    'table': self,
                    'objects': objects,
                },
            )
        )