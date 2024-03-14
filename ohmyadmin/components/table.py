from __future__ import annotations

import enum
import typing

from starlette.datastructures import URL
from starlette.requests import Request

from ohmyadmin.components.base import Component
from ohmyadmin.components.text import Text
from ohmyadmin.ordering import SortingHelper
from ohmyadmin.routing import resolve_url, URLType
from ohmyadmin.templating import render_to_string


class CellAlign(enum.StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class TableHeadCell(Component):
    template_name: str = "ohmyadmin/components/table/table_head_cell.html"

    def __init__(
        self,
        text: str,
        align: CellAlign = CellAlign.LEFT,
    ) -> None:
        self.text = text
        self.align = align
        self.child = Text(text)


class TableSortableHeadCell(TableHeadCell):
    template_name = "ohmyadmin/components/table/table_sortable_head_cell.html"

    def __init__(
        self,
        text: str,
        sort_field: str,
        align: CellAlign = CellAlign.LEFT,
        query_param: str = "ordering",
    ) -> None:
        super().__init__(text=text, align=align)
        self.sort_field = sort_field
        self.query_param = query_param

    def render(self, request: Request) -> str:
        helper = SortingHelper(request, self.query_param)
        return render_to_string(
            request,
            self.template_name,
            {
                "component": self,
                "helper": helper,
            },
        )


T = typing.TypeVar("T")


class TableColumn(Component):
    template_name: str = "ohmyadmin/components/table/table_cell.html"

    def __init__(self, child: Component, align: CellAlign = CellAlign.LEFT, colspan: int = 1) -> None:
        self.child = child
        self.align = align
        self.colspan = colspan


_ROW = typing.TypeVar("_ROW", bound=TableHeadCell | TableColumn)


class TableRow(Component, typing.Generic[_ROW]):
    template_name: str = "ohmyadmin/components/table/table_row.html"

    def __init__(self, children: typing.Iterable[_ROW]) -> None:
        self.children = children


class Table(Component, typing.Generic[T]):
    template_name: str = "ohmyadmin/components/table/table.html"

    def __init__(
        self,
        items: typing.Iterable[T],
        header: TableRow[TableHeadCell],
        row_builder: typing.Callable[[T], TableRow[TableColumn]],
        summary: typing.Sequence[TableColumn] | None = None,
    ) -> None:
        self.items = items
        self.header = header
        self.summary = summary
        self.row_builder = row_builder

    def build_cells(self, item: T) -> TableRow:
        return self.row_builder(item)

    @property
    def rows(self) -> typing.Iterable[TableRow]:
        for item in self.items:
            yield self.row_builder(item)


class RowActions(Component):
    template_name: str = "ohmyadmin/components/table/row_actions.html"


class LinkRowAction(Component):
    template_name: str = "ohmyadmin/components/table/table_row_action_link.html"

    def __init__(self, url: URLType, label: str, icon: str) -> None:
        self.url = url
        self.label = label
        self.icon = icon

    def resolve(self, request: Request) -> URL:
        return resolve_url(request, self.url)
