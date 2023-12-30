import typing

from ohmyadmin.screens.index import IndexScreen
from ohmyadmin.views.base import IndexView
from ohmyadmin.views.table import TableView
from ohmyadmin.display_fields import DisplayField


class TableScreen(IndexScreen):
    columns: typing.Sequence[DisplayField] = tuple()

    def get_view(self) -> IndexView:
        return TableView(columns=self.columns)
