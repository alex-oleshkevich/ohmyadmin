import typing

from ohmyadmin.screens.index import IndexScreen
from ohmyadmin.views.base import IndexView
from ohmyadmin.views.table import Column, TableView


class TableScreen(IndexScreen):
    columns: typing.Sequence[Column] = tuple()

    def get_view(self) -> IndexView:
        return TableView(columns=self.columns)
