from __future__ import annotations

import typing
from sqlalchemy.orm import InstrumentedAttribute
from starlette.requests import Request

from ohmyadmin.components import Component
from ohmyadmin.helpers import media_url, render_to_string
from ohmyadmin.ordering import SortingHelper

Formatter = typing.Callable[[typing.Any], str]
BadgeColors = typing.Literal['red', 'green', 'blue', 'pink', 'teal', 'sky', 'yellow', 'gray']
RowActionsCallback = typing.Callable[[typing.Any], typing.Iterable[Component]]


class Column:
    name: str
    label: str
    sortable: bool = False
    searchable: bool = False
    head_template: str = 'ohmyadmin/tables/cell_head.html'
    template: str = 'ohmyadmin/tables/cell_text.html'

    def __init__(
        self,
        name: str,
        *,
        label: str = '',
        sortable: bool = False,
        searchable: bool = False,
        source: str = '',
        value_format: str | Formatter | None = None,
        sort_by: InstrumentedAttribute | None = None,
        search_in: list[InstrumentedAttribute] | None = None,
        link: bool = False,
        link_factory: typing.Callable[[Request, typing.Any], str] | None = None,
    ) -> None:
        self.name = name
        self.label = label or name.replace('_', ' ').title()
        self.sortable = sortable
        self.searchable = searchable
        self.source = source or name
        self.value_format = value_format
        self.sort_by = sort_by
        self.search_in = search_in or []
        self.link = link
        self.link_factory = link_factory

    @property
    def has_link(self) -> bool:
        return self.link is True or self.link_factory is not None

    def get_link(self, request: Request, entity: typing.Any) -> str:
        if self.link_factory:
            return self.link_factory(request, entity)
        route = request.state.resource.get_route_name('edit')
        pk = request.state.resource.get_pk_value(entity)
        return request.url_for(route, pk=pk)

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

    def get_sorting_key(self) -> str:
        if self.sort_by:
            return str(self.sort_by.key)
        return self.name

    def render_head_cell(self, request: Request, sorting_helper: SortingHelper) -> str:
        return render_to_string(
            self.head_template,
            {
                'column': self,
                'request': request,
                'sorting_helper': sorting_helper,
            },
        )

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
