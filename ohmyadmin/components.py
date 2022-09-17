from __future__ import annotations

import abc
import typing
import wtforms

from ohmyadmin.actions import Action
from ohmyadmin.forms import ListField
from ohmyadmin.helpers import render_to_string
from ohmyadmin.i18n import _

Colspan = int | typing.Literal['full']


class Component(abc.ABC):
    template = ''

    def render(self) -> str:
        if not self.template:
            raise ValueError(f'Layout {self.__class__.__name__} does not define template name.')
        return render_to_string(self.template, {'element': self})

    __str__ = render


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


class FormElement(Component):
    template = 'ohmyadmin/components/form_field.html'

    def __init__(self, field: wtforms.Field, colspan: Colspan = 1) -> None:
        self.field = field
        self.colspan = colspan


class FormPlaceholder(Component):
    template = 'ohmyadmin/components/form_placeholder.html'

    def __init__(self, label: str, text: str, colspan: Colspan = 1) -> None:
        self.text = text
        self.label = label
        self.colspan = colspan


class FormRepeater(Component):
    template = 'ohmyadmin/components/form_repeater.html'

    def __init__(self, form: wtforms.FieldList, layout_builder: typing.Callable[[ListField], Component]) -> None:
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
                    'x-bind:id': '`%s`' % field.id.replace('0', '${index}'),
                    'x-bind:name': '`%s`' % field.name.replace('0', '${index}'),
                }
            )
        return self.layout_builder(form)

    def __iter__(self) -> typing.Iterator[Component]:
        for field in self.form:
            yield self.layout_builder(field)

    def __len__(self) -> int:
        return len(self.form)


class EmptyState(Component):
    template = 'ohmyadmin/components/empty_state.html'

    def __init__(
        self,
        message: str,
        actions: list[Action],
        heading: str = _('Empty page'),
        image_template: str = 'ohmyadmin/images/empty.svg',
    ) -> None:
        self.heading = heading
        self.message = message
        self.actions = actions
        self.image_template = image_template
