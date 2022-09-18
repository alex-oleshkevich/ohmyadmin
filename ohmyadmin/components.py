from __future__ import annotations

import abc
import typing
import wtforms

from ohmyadmin.forms import ListField
from ohmyadmin.globals import get_current_request
from ohmyadmin.helpers import render_to_string
from ohmyadmin.i18n import _
from ohmyadmin.structures import URLSpec

if typing.TYPE_CHECKING:
    from ohmyadmin.actions import BaseAction

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
        actions: list[Component],
        heading: str = _('Empty page'),
        image_template: str = 'ohmyadmin/images/empty.svg',
    ) -> None:
        self.heading = heading
        self.message = message
        self.actions = actions
        self.image_template = image_template


class ButtonLink(Component):
    """
    A link that looks like a button.

    Commonly used as action button that performs a redirect to another page. A
    good example is: 'Add new object' primary action on index pages.
    """

    template = 'ohmyadmin/components/button_link.html'

    def __init__(
        self,
        url: str | URLSpec,
        text: str = '',
        icon: str = '',
        color: ButtonColor = 'default',
    ) -> None:
        assert text or icon, 'ButtonLink component requires either text or icon argument set.'

        self.text = text
        self.icon = icon
        self.color = color
        self.url_spec = URLSpec(url=url) if isinstance(url, str) else url

    @property
    def url(self) -> str:
        return self.url_spec.to_url()


class Button(Component):
    """Renders a button."""

    template = 'ohmyadmin/components/button.html'

    def __init__(
        self,
        text: str = '',
        icon: str = '',
        color: ButtonColor = 'default',
        type: ButtonType = 'submit',
        name: str | None = None,
    ) -> None:
        assert text or icon, 'Button component requires either text or icon argument set.'

        self.text = text
        self.icon = icon
        self.type = type
        self.name = name
        self.color = color


class RowAction(Component):
    def __init__(
        self,
        entity: typing.Any,
        text: str = '',
        icon: str = '',
        url: str | URLSpec | None = None,
        action: BaseAction | None = None,
        danger: bool = False,
        children: list[Component] | None = None,
    ):
        text = text or (action.label if action else '')
        icon = icon or (action.icon if action else '')
        if children:
            icon = icon or 'dots'
        assert text or icon, 'RowAction: Either text or icon argument must be passed.'
        assert url or action or children, 'RowAction: Either action or url, or children argument must be passed.'

        self.text = text
        self.icon = icon
        self.entity = entity
        self.action = action
        self.children = children
        self.color = 'danger' if danger else 'default'
        self.url_spec = typing.cast(URLSpec, URLSpec(url=url) if isinstance(url, str) else url)

    @property
    def url(self) -> str:
        return self.url_spec.to_url()

    def get_template(self) -> str:
        if self.children:
            return 'ohmyadmin/components/row_action_group.html'

        if self.action:
            return 'ohmyadmin/components/row_action_action.html'

        return 'ohmyadmin/components/row_action_link.html'


class MenuItem(Component):
    template = 'ohmyadmin/components/menu_item.html'

    def __init__(self, text: str, url: str | URLSpec, icon: str = '') -> None:
        self.text = text
        self.icon = icon
        self.url_spec = URLSpec(url=url) if isinstance(url, str) else url

    @property
    def url(self) -> str:
        return self.url_spec.to_url()

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
