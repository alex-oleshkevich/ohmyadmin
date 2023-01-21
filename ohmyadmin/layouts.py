import abc
import typing
import wtforms
from starlette.requests import Request

from ohmyadmin.shortcuts import render_to_string


class Layout(abc.ABC):
    @abc.abstractmethod
    def render(self, request: Request) -> str:
        ...


class Grid(Layout):
    def __init__(self, children: typing.Sequence[Layout], columns: int = 2, gap: int = 6) -> None:
        self.gap = gap
        self.columns = columns
        self.children = children

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/layouts/grid.html', {'layout': self})


class Column(Layout):
    def __init__(self, children: typing.Sequence[Layout], gap: int = 5, colspan: int | str = '') -> None:
        self.gap = gap
        self.colspan = colspan
        self.children = children

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/layouts/column.html', {'layout': self})


class Row(Layout):
    def __init__(self, children: typing.Sequence[Layout], gap: int = 5) -> None:
        self.gap = gap
        self.children = children

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/layouts/row.html', {'layout': self})


class Card(Layout):
    def __init__(
        self, children: typing.Sequence[Layout], label: str = '', description: str = '', columns: int = 1, gap: int = 5
    ) -> None:
        self.label = label
        self.gap = gap
        self.columns = columns
        self.children = children
        self.description = description

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/layouts/card.html', {'layout': self})


class FieldSet(Layout):
    def __init__(self, children: typing.Sequence[Layout], label: str = '', description: str = '') -> None:
        self.label = label
        self.children = children
        self.description = description

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/layouts/fieldset.html', {'layout': self})


class Input(Layout):
    def __init__(self, field: wtforms.Field, max_width: str = 'sm', colspan: str | int = '') -> None:
        self.field = field
        self.colspan = colspan
        self.max_width = max_width

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/layouts/input.html', {'layout': self})


class SimpleForm(Layout):
    def __init__(self, children: typing.Sequence[Input], label: str = '', description: str = '') -> None:
        self.children = children
        self.label = label
        self.description = description

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/layouts/simple_form.html', {'layout': self})


class StackedForm(Layout):
    def __init__(self, children: typing.Sequence[Input], label: str = '', description: str = '') -> None:
        self.children = children
        self.label = label
        self.description = description

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/layouts/stacked_form.html', {'layout': self})
