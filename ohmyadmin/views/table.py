from __future__ import annotations
import dataclasses
import typing

from starlette.requests import Request

from ohmyadmin.actions import actions
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.contracts import HasObjectActions, HasOrderingFields, HasOrderingParam, HasBatchActions
from ohmyadmin.ordering import SortingHelper
from ohmyadmin.screens import Screen
from ohmyadmin.templating import render_to_string
from ohmyadmin.views.base import IndexView


@dataclasses.dataclass
class TableContext:
    batch_actions: typing.Sequence[actions.ModalAction]
    object_actions: typing.Sequence[actions.Action]
    columns: typing.Sequence[DecoratedColumn]
    sorting: SortingHelper
    screen: Screen

    @property
    def has_batch_actions(self) -> bool:
        return len(self.batch_actions) > 0

    @property
    def has_object_actions(self) -> bool:
        return len(self.object_actions) > 0


class DecoratedColumn:
    def __init__(self, column: DisplayField, sortable: bool) -> None:
        self.column = column
        self.sortable = sortable

    def __getattr__(self, item: str) -> typing.Any:
        return getattr(self.column, item)


class TableView(IndexView):
    template = "ohmyadmin/views/table/table.html"

    def __init__(self, columns: typing.Sequence[DisplayField]) -> None:
        self.columns = columns

    def render(self, request: Request, screen: Screen, models: typing.Sequence[typing.Any]) -> str:
        ordering_param = screen.get_ordering_param() if isinstance(screen, HasOrderingParam) else "ordering"
        batch_actions = screen.get_batch_actions() if isinstance(screen, HasBatchActions) else []
        object_actions = screen.get_object_actions() if isinstance(screen, HasObjectActions) else []
        ordering_fields = screen.get_ordering_fields() if isinstance(screen, HasOrderingFields) else []
        ordering = SortingHelper(request, ordering_param)

        columns = [
            DecoratedColumn(
                column=column,
                sortable=column.name in ordering_fields,
            )
            for column in self.columns
        ]

        return render_to_string(
            request,
            self.template,
            {
                "models": models,
                "view": TableContext(
                    screen=screen,
                    sorting=ordering,
                    columns=columns,
                    batch_actions=batch_actions,
                    object_actions=object_actions,
                ),
            },
        )
