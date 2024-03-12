from __future__ import annotations

import typing

from ohmyadmin.components.base import Component

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
