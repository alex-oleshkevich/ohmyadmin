from __future__ import annotations

from ohmyadmin.components.base import Component


class Column(Component):
    template_name: str = "ohmyadmin/components/layout/column.html"

    def __init__(
        self,
        children: list[Component],
        gap: int = 3,
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
