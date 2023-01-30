import functools
import typing
from markupsafe import Markup
from starlette.requests import Request
from unittest import mock

from ohmyadmin import actions
from ohmyadmin.formatters import DataFormatter, StringFormatter
from ohmyadmin.helpers import LazyObjectURL, LazyURL, snake_to_sentence
from ohmyadmin.ordering import SortingHelper
from ohmyadmin.pagination import Pagination
from ohmyadmin.shortcuts import render_to_string
from ohmyadmin.views.base import IndexView


def default_value_getter(obj: typing.Any, attr: str) -> typing.Any:
    return getattr(obj, attr, 'undefined!')


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
        link: bool | str | LazyURL | LazyObjectURL | None = None,
        value_getter: typing.Callable[[typing.Any], typing.Any] | None = None,
    ) -> None:
        self.link = link
        self.name = name
        self.sortable = sortable
        self.searchable = searchable
        self.search_in = search_in or name
        self.sort_by = sort_by or name
        self.formatter = formatter or StringFormatter()
        self.label = label or snake_to_sentence(name)
        self.value_getter = value_getter or functools.partial(default_value_getter, attr=self.name)

    def get_value(self, obj: typing.Any) -> typing.Any:
        return self.value_getter(obj)

    def format_value(self, request: Request, value: typing.Any) -> str:
        return self.formatter(request, value)

    def render(self, request: Request, obj: typing.Any) -> str:
        value = self.get_value(obj)
        display_value = self.format_value(request, value)
        link: str = ''
        match self.link:
            case str():
                link = self.link
            case bool():
                link = request.state.page.generate_url(request)
            case LazyURL():
                link = str(self.link.resolve(request))
            case LazyObjectURL():
                link = str(self.link.resolve(request, obj))

        return request.state.admin.render_to_string(
            request,
            'ohmyadmin/views/table/table_cell.html',
            {
                'link': link,
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
    def __init__(self, columns: typing.Sequence[TableColumn]) -> None:
        self.columns = columns

    def get_object_actions(self, request: Request, obj: typing.Any) -> typing.Sequence[actions.ObjectAction]:
        return request.state.page.get_object_actions(request, obj)

    def render(self, request: Request, objects: Pagination[typing.Any]) -> str:
        request.state.table_sorting = SortingHelper(request, request.state.page.ordering_param)
        has_object_actions = self.get_object_actions(request, mock.MagicMock())
        has_batch_actions = bool(request.state.page.get_batch_actions(request))
        return Markup(
            render_to_string(
                request,
                'ohmyadmin/views/table/table.html',
                {
                    'table': self,
                    'objects': objects,
                    'has_batch_actions': has_batch_actions,
                    'has_object_actions': has_object_actions,
                },
            )
        )
