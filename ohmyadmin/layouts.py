import abc
import typing
import wtforms
from starlette.requests import Request

from ohmyadmin.shortcuts import render_to_string


class Layout(abc.ABC):
    @abc.abstractmethod
    def render(self, request: Request) -> str:  # pragma: no cover
        ...


class TemplateLayout(Layout):
    template: str

    def render(self, request: Request) -> str:
        assert self.template, 'template is undefined'
        return render_to_string(request, self.template, {'layout': self})


class Grid(TemplateLayout):
    template = 'ohmyadmin/layouts/grid.html'

    def __init__(self, children: typing.Sequence[Layout], columns: int = 2, gap: int = 6) -> None:
        self.gap = gap
        self.columns = columns
        self.children = children


class Column(TemplateLayout):
    template = 'ohmyadmin/layouts/column.html'

    def __init__(self, children: typing.Sequence[Layout], gap: int = 5, colspan: int | str = '') -> None:
        self.gap = gap
        self.colspan = colspan
        self.children = children


class Row(TemplateLayout):
    template = 'ohmyadmin/layouts/row.html'

    def __init__(self, children: typing.Sequence[Layout], gap: int = 5) -> None:
        self.gap = gap
        self.children = children


class Card(TemplateLayout):
    template = 'ohmyadmin/layouts/card.html'

    def __init__(self, children: typing.Sequence[Layout], label: str = '', description: str = '') -> None:
        self.label = label
        self.children = children
        self.description = description


class SideSection(TemplateLayout):
    template = 'ohmyadmin/layouts/fieldset.html'

    def __init__(self, children: typing.Sequence[Layout], label: str = '', description: str = '') -> None:
        self.label = label
        self.children = children
        self.description = description


class Input(TemplateLayout):
    template = 'ohmyadmin/layouts/input.html'

    def __init__(self, field: wtforms.Field, max_width: str = 'full', colspan: str | int = '') -> None:
        self.field = field
        self.colspan = colspan
        self.max_width = max_width


class RowFormLayout(TemplateLayout):
    template = 'ohmyadmin/layouts/simple_form.html'

    def __init__(self, children: typing.Sequence[Input], label: str = '', description: str = '') -> None:
        self.children = children
        self.label = label
        self.description = description


class StackedForm(TemplateLayout):
    template = 'ohmyadmin/layouts/stacked_form.html'

    def __init__(self, children: typing.Sequence[Input], label: str = '', description: str = '') -> None:
        self.children = children
        self.label = label
        self.description = description


class Text(Layout):
    def __init__(self, content: str) -> None:
        self.content = content

    def render(self, request: Request) -> str:
        return self.content
