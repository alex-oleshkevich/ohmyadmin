from __future__ import annotations

import typing
from starlette.requests import Request

from ohmyadmin.components import Component
from ohmyadmin.helpers import media_url, render_to_string

Formatter = typing.Callable[[typing.Any], str]
BadgeColors = typing.Literal['red', 'green', 'blue', 'pink', 'teal', 'sky', 'yellow', 'gray']
RowActionsCallback = typing.Callable[[typing.Any], typing.Iterable[Component]]


class Column:
    name: str
    label: str
    sortable: bool = False
    searchable: bool = False
    template: str = 'ohmyadmin/tables/cell_text.html'

    def __init__(
        self,
        name: str,
        *,
        label: str = '',
        sortable: bool = False,
        sort_by: str = '',
        searchable: bool = False,
        search_in: str = '',
        source: str = '',
        value_format: str | Formatter | None = None,
        link: bool = False,
        link_factory: typing.Callable[[Request, typing.Any], str] | None = None,
        **kwargs: typing.Any,
    ) -> None:
        self.name = name
        self.label = label or name.replace('_', ' ').title()
        self.source = source or name
        self.value_format = value_format
        self.link = link or link_factory is not None
        self.link_factory = link_factory
        self.sort_by = sort_by if sort_by else self.name
        self.search_in = search_in if search_in else self.name
        self.sortable = sortable
        self.searchable = searchable

    def get_value(self, obj: typing.Any) -> typing.Any:
        parts = self.source.split('.')
        value = obj
        try:
            for part in parts:
                value = getattr(value, part)
        except AttributeError:
            value = ''
        return value

    def format_value(self, value: typing.Any) -> str:
        if callable(self.value_format):
            return self.value_format(value)
        if self.value_format:
            return self.value_format % value
        return value

    def get_display_value(self, obj: typing.Any) -> str:
        return self.format_value(self.get_value(obj))

    def render(self, entity: typing.Any) -> str:
        return render_to_string(self.template, {'column': self, 'object': entity})

    def __call__(self, entity: typing.Any) -> str:
        return self.render(entity)


class NumberColumn(Column):
    template: str = 'ohmyadmin/tables/cell_number.html'


class BoolColumn(Column):
    template: str = 'ohmyadmin/tables/cell_bool.html'


class ImageColumn(Column):
    template: str = 'ohmyadmin/tables/cell_image.html'

    def get_display_value(self, obj: typing.Any) -> str:
        value = self.format_value(self.get_value(obj))
        if value.startswith('http://') or value.startswith('https://'):
            return value

        return media_url(self.get_value(obj))


class DateColumn(Column):
    template: str = 'ohmyadmin/tables/cell_date.html'

    def __init__(self, name: str, format: str = '%d %B, %Y', **kwargs: typing.Any) -> None:
        kwargs['value_format'] = lambda x: x.strftime(format)
        super().__init__(name, **kwargs)


class BadgeColumn(Column):
    template: str = 'ohmyadmin/tables/cell_badge.html'

    def __init__(self, name: str, colors: dict[str, str] | None, **kwargs: typing.Any) -> None:
        super().__init__(name, **kwargs)
        self.colors = colors or {}

    def render(self, entity: typing.Any) -> str:
        value = self.get_display_value(entity)
        color = self.colors.get(value, 'gray')
        return render_to_string(self.template, {'column': self, 'object': entity, 'color': color})


class HasManyColumn(Column):
    def __init__(self, name: str, child: Column, **kwargs: typing.Any) -> None:
        self.child = child
        super().__init__(name, **kwargs)

    def render(self, entity: typing.Any) -> str:
        values = self.get_value(entity)
        value = values[0] if values else None
        return self.child.render(value)


class ActionColumn(Column):
    template: str = 'ohmyadmin/tables/cell_actions.html'

    def __init__(self, actions: RowActionsCallback) -> None:
        self.actions = actions
        super().__init__('__actions__')

    def get_value(self, obj: typing.Any) -> typing.Any:
        return ''

    def get_actions(self, entity: typing.Any) -> typing.Iterable[Component]:
        yield from self.actions(entity)


def get_search_value(request: Request, param_name: str) -> str:
    return request.query_params.get(param_name, '').strip()
