from __future__ import annotations

import typing

from starlette.requests import Request

from ohmyadmin import formatters
from ohmyadmin.components.base import Component
from ohmyadmin.components.text import Text

T = typing.TypeVar("T")


class Column(Component):
    template_name: str = "ohmyadmin/components/layout/column.html"

    def __init__(
        self,
        children: list[Component],
        gap: int = 0,
        colspan: int = 12,
    ) -> None:
        self.gap = gap
        self.colspan = colspan
        self.children = children


class Grid(Component):
    template_name: str = "ohmyadmin/components/layout/grid.html"

    def __init__(
        self,
        children: list[Component],
        columns: int = 12,
        gap: int = 5,
        colspan: int = 12,
    ) -> None:
        self.gap = gap
        self.colspan = colspan
        self.columns = columns
        self.children = children


class Group(Component):
    template_name: str = "ohmyadmin/components/group.html"

    def __init__(
        self,
        children: list[Component],
        label: str = "",
        description: str = "",
        colspan: int = 12,
        gap: int = 2,
    ) -> None:
        self.gap = gap
        self.label = label
        self.colspan = colspan
        self.children = children
        self.description = description


class Table(Component, typing.Generic[T]):
    template_name: str = "ohmyadmin/components/table.html"

    def __init__(
        self,
        headers: typing.Sequence[str],
        items: typing.Sequence[T],
        row_builder: typing.Callable[[T], typing.Sequence[TableCell[T]]],
        summary: typing.Sequence[TableCell] | None = None,
    ) -> None:
        self.items = items
        self.headers = headers
        self.row_builder = row_builder
        self.summary = summary

    def build_cells(self, item: T) -> typing.Sequence[TableCell[T]]:
        return self.row_builder(item)


class TableCell(Component, typing.Generic[T]):
    template_name: str = "ohmyadmin/components/table_cell.html"

    def __init__(
        self,
        value: T = None,
        formatter: formatters.ValueFormatter = formatters.Auto(),
        value_builder: typing.Callable[[T], Component] | None = None,
        empty_value: str = "-",
        align: typing.Literal["left", "center", "right"] = "left",
        colspan: int = 1,
    ) -> None:
        self.value = empty_value if value is None else value
        self.align = align
        self.formatter = formatter
        self.colspan = colspan
        self.value_builder = value_builder

    def build_value(self, request: Request) -> Component:
        if self.value_builder:
            return self.value_builder(self.value)

        formatted_value = self.formatter(request, self.value)
        return Text(formatted_value)
