import abc
import datetime
import typing
from starlette.requests import Request

from ohmyadmin.templating import macro

LinkFactory = typing.Callable[[Request, typing.Any], str]
ValueGetter = typing.Callable[[typing.Any], typing.Any]


class DisplayComponent:
    @abc.abstractmethod
    def render(self, value: typing.Any) -> str:
        ...

    def __call__(self, value: typing.Any) -> str:
        return self.render(value)


class Text(DisplayComponent):
    def render(self, value: typing.Any) -> str:
        return str(value)


class Link(DisplayComponent):
    def __init__(self, href: str) -> None:
        self.href = href

    def render(self, value: typing.Any) -> str:
        macros = macro('ohmyadmin/components/display.html', 'link')
        return macros(self.href, text=value)


class Image(DisplayComponent):
    def __init__(self, height: int = 40, width: int | None = None, lazy: bool = False) -> None:
        self.lazy = lazy
        self.width = width
        self.height = height

    def render(self, value: typing.Any) -> str:
        macros = macro('ohmyadmin/components/display.html', 'image')
        return macros(value, height=self.height, width=self.width, lazy=self.lazy)


class Boolean(DisplayComponent):
    def render(self, value: typing.Any) -> str:
        macros = macro('ohmyadmin/components/display.html', 'boolean')
        return macros(value)


class DateTime(DisplayComponent):
    def __init__(self, format: str = '%d %B, %Y') -> None:
        self.format = format

    def render(self, value: str) -> str:
        date_value = datetime.datetime.fromisoformat(value)
        return date_value.strftime(self.format)


class Number(DisplayComponent):
    def render(self, value: str) -> str:
        return '<div class="text-right">{value}</div>'.format(value=value)


class Money(DisplayComponent):
    def __init__(self, currency: str, placement: typing.Literal['left', 'right'] = 'left') -> None:
        self.currency = currency
        self.placement = placement

    def render(self, value: str) -> str:
        prefix = f'{self.currency} ' if self.placement == 'left' else ''
        suffix = f' {self.currency}' if self.placement == 'right' else ''
        return '<div class="text-right">{prefix}{value}{suffix}</div>'.format(value=value, prefix=prefix, suffix=suffix)


BadgeColor = typing.Literal['blue', 'green', 'yellow', 'green', 'red', 'pink', 'teal', 'sky', 'gray']


class Badge(DisplayComponent):
    def __init__(self, colors: dict[str, str]) -> None:
        self.colors = colors

    def render(self, value: typing.Any) -> str:
        color = self.colors.get(value, 'gray')
        macros = macro('ohmyadmin/components/display.html', 'badge')
        return macros(value, color)


def string_formatter(value: typing.Any) -> str:
    return str(value)


class DisplayField:
    def __init__(
        self,
        name: str,
        label: str = '',
        sortable: bool = False,
        sort_by: str = '',
        searchable: bool = False,
        search_in: str = '',
        link: bool | LinkFactory = False,
        value_getter: ValueGetter | None = None,
        value_formatter: str | typing.Callable[[typing.Any], str] = '{value}',
        component: DisplayComponent | None = None,
    ) -> None:
        self.name = name
        self.link = link
        self.sortable = sortable
        self.sort_by = sort_by or name
        self.searchable = searchable
        self.search_in = search_in or name
        self.component = component or Text()
        self.label = label or name.replace('_', ' ').capitalize()
        self.value_getter = value_getter or (lambda obj: getattr(obj, name))
        self.value_formatter = value_formatter

    def get_value(self, entity: typing.Any) -> str:
        return self.value_getter(entity)

    def render(self, request: Request, entity: typing.Any) -> str:
        value = self.get_value(entity)
        if callable(self.value_formatter):
            value = self.value_formatter(value)
        else:
            value = self.value_formatter.format(value=value)

        if self.link:
            if callable(self.link):
                href = self.link(request, entity)
            else:
                pk = request.state.resource.get_pk_value(entity)
                path_name = request.state.resource.url_name('edit')
                href = request.url_for(path_name, pk=pk)
            value = Link(href).render(value)

        return self.component.render(value)
