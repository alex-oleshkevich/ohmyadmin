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
        macros = macro('ohmyadmin/display.html', 'link')
        return macros(self.href, text=value)


class Image(DisplayComponent):
    def __init__(
        self,
        height: int = 40,
        width: int | None = None,
        lazy: bool = False,
        url_generator: typing.Callable[[str], str] | None = None,
    ) -> None:
        self.lazy = lazy
        self.width = width
        self.height = height
        self.url_generator = url_generator

    def render(self, value: typing.Any) -> str:
        value = self.url_generator(value) if self.url_generator is not None else value
        macros = macro('ohmyadmin/display.html', 'image')
        return macros(value, height=self.height, width=self.width, lazy=self.lazy)


class Boolean(DisplayComponent):
    def render(self, value: typing.Any) -> str:
        macros = macro('ohmyadmin/display.html', 'boolean')
        return macros(value)


class DateTime(DisplayComponent):
    def __init__(self, format: str = '%d %B, %Y') -> None:
        self.format = format

    def render(self, value: datetime.datetime | str) -> str:
        value = datetime.datetime.fromisoformat(value) if isinstance(value, str) else value
        return value.strftime(self.format)


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
        macros = macro('ohmyadmin/display.html', 'badge')
        return macros(value, color)


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

    def get_value(self, entity: typing.Any) -> str:
        return self.value_getter(entity)

    def render(self, request: Request, entity: typing.Any) -> str:
        value = self.get_value(entity)

        if self.link:
            if callable(self.link):
                href = self.link(request, entity)
            else:
                pk = request.state.resource.get_pk_value(entity)
                path_name = request.state.resource.url_name('edit')
                href = request.url_for(path_name, pk=pk)
            value = Link(href).render(value)

        return self.component.render(value)
