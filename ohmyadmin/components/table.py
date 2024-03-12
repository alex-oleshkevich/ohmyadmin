from __future__ import annotations

import enum
import typing

from starlette.requests import Request

from ohmyadmin import formatters
from ohmyadmin.components import Component, T, Text
from ohmyadmin.ordering import SortingHelper
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


class TableColumn(Component, typing.Generic[T]):
    template_name: str = "ohmyadmin/components/table_cell.html"

    def __init__(
        self,
        value: T = None,
        formatter: formatters.ValueFormatter = formatters.Auto(),
        value_builder: typing.Callable[[], Component] | None = None,
        empty_value: str = "-",
        align: CellAlign = CellAlign.LEFT,
        colspan: int = 1,
    ) -> None:
        self.value = empty_value if value is None else value
        self.align = align
        self.formatter = formatter
        self.colspan = colspan
        self.value_builder = value_builder

    def build_value(self, request: Request) -> Component:
        if self.value_builder:
            return self.value_builder()

        formatted_value = self.formatter(request, self.value)
        return Text(formatted_value)


_ROW = typing.TypeVar("_ROW", bound=TableHeadCell | TableColumn)


class TableRow(Component, typing.Generic[_ROW]):
    template_name: str = "ohmyadmin/components/table/table_row.html"

    def __init__(self, children: typing.Iterable[_ROW]) -> None:
        self.children = children


class Table(Component, typing.Generic[T]):
    template_name: str = "ohmyadmin/components/table.html"

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
