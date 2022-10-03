from __future__ import annotations

import abc
import typing
import wtforms
from starlette.datastructures import URL

from ohmyadmin.forms import FieldList
from ohmyadmin.globals import get_current_request
from ohmyadmin.helpers import render_to_string

Colspan = int | typing.Literal['full']
ButtonColor = typing.Literal['default', 'primary', 'text', 'danger']
ButtonType = typing.Literal['submit', 'button']


class Component(abc.ABC):
    template = ''

    def get_template(self) -> str:
        if not self.template:
            raise ValueError(f'Layout {self.__class__.__name__} does not define template name.')
        return self.template

    def render(self) -> str:
        return render_to_string(self.get_template(), {'element': self})

    def __str__(self) -> str:
        return self.render()


class Grid(Component):
    template = 'ohmyadmin/components/grid.html'

    def __init__(self, children: typing.Iterable[Component], columns: int = 1, gap: int = 5) -> None:
        self.cols = columns
        self.gap = gap
        self.children = children

    def __iter__(self) -> typing.Iterator[Component]:
        return iter(self.children)


class Group(Component):
    template = 'ohmyadmin/components/group.html'

    def __init__(self, children: typing.Iterable[Component], colspan: Colspan = 'full', columns: int = 1) -> None:
        self.colspan = colspan
        self.columns = columns
        self.children = children

    def __iter__(self) -> typing.Iterator[Component]:
        return iter(self.children)


class Card(Component):
    template = 'ohmyadmin/components/card.html'

    def __init__(
        self,
        children: typing.Iterable[Component],
        title: str = '',
        columns: int = 1,
    ) -> None:
        self.title = title
        self.columns = columns
        self.children = children

    def __iter__(self) -> typing.Iterator[Component]:
        return iter(self.children)


class Row(Component):
    """Groups child components in a row."""

    template = 'ohmyadmin/components/row.html'

    def __init__(
        self,
        children: typing.Iterable[Component],
        columns: int = 1,
        colspan: Colspan = 'full',
    ) -> None:
        self.columns = columns
        self.colspan = colspan
        self.children = children

    def __iter__(self) -> typing.Iterator[Component]:
        return iter(self.children)


class FormElement(Component):
    template = 'ohmyadmin/components/form_field.html'

    def __init__(
        self,
        field: wtforms.Field,
        colspan: Colspan = 1,
        horizontal: bool = False,
    ) -> None:
        self.field = field
        self.colspan = colspan
        self.horizontal = horizontal

    @property
    def render_label(self) -> bool:
        return not isinstance(self.field, (wtforms.HiddenField, wtforms.BooleanField))


class FormPlaceholder(Component):
    template = 'ohmyadmin/components/form_placeholder.html'

    def __init__(self, label: str, text: str, colspan: Colspan = 1) -> None:
        self.text = text
        self.label = label
        self.colspan = colspan


class FormRepeater(Component):
    template = 'ohmyadmin/components/form_repeater.html'

    def __init__(self, form: wtforms.FieldList, layout_builder: typing.Callable[[FieldList], Component]) -> None:
        self.form = form
        self.layout_builder = layout_builder

    @property
    def empty(self) -> Component:
        form_field = next(iter(self.form))
        form = form_field.form
        form.process(None)
        for field in form:
            field.render_kw = field.render_kw or {}
            field.render_kw.update(
                {
                    'x-bind:id': '`%s`' % field.slug.replace('0', '${index}'),
                    'x-bind:name': '`%s`' % field.name.replace('0', '${index}'),
                }
            )
        return self.layout_builder(form)

    def __iter__(self) -> typing.Iterator[Component]:
        for field in self.form:
            yield self.layout_builder(field)

    def __len__(self) -> int:
        return len(self.form)


class MenuItem(Component):
    template = 'ohmyadmin/components/menu_item.html'

    def __init__(self, text: str, url: str | URL, icon: str = '') -> None:
        self.text = text
        self.icon = icon
        self.url = str(url)

    @property
    def is_active(self) -> bool:
        request = get_current_request()
        return str(request.url).startswith(self.url)


class MenuGroup(Component):
    template = 'ohmyadmin/components/menu_group.html'

    def __init__(self, text: str, items: list[MenuItem], icon: str = '') -> None:
        self.text = text
        self.items = items
        self.icon = icon

    def __iter__(self) -> typing.Iterator[MenuItem]:
        yield from self.items
