import abc
import typing
from starlette.requests import Request

from ohmyadmin.templating import macro

LinkFactory = typing.Callable[[Request, typing.Any], str]
ValueGetter = typing.Callable[[typing.Any], typing.Any]


class ListComponent:
    @abc.abstractmethod
    def render(self, value: typing.Any) -> str:
        ...

    def __call__(self, value: typing.Any) -> str:
        return self.render(value)


class Text(ListComponent):
    def render(self, value: typing.Any) -> str:
        return str(value)


class Link(ListComponent):
    def __init__(self, href: str) -> None:
        self.href = href

    def render(self, value: typing.Any) -> str:
        macros = macro('ohmyadmin/components/display.html', 'link')
        return macros(self.href, text=value)


class Image(ListComponent):
    def __init__(self, height: int = 40, width: int | None = None, lazy: bool = False) -> None:
        self.lazy = lazy
        self.width = width
        self.height = height

    def render(self, value: typing.Any) -> str:
        macros = macro('ohmyadmin/components/display.html', 'image')
        return macros(value, height=self.height, width=self.width, lazy=self.lazy)


class Boolean(ListComponent):
    def render(self, value: typing.Any) -> str:
        macros = macro('ohmyadmin/components/display.html', 'boolean')
        return macros(value)


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
        component: ListComponent | None = None,
    ) -> None:
        self.name = name
        self.link = link
        self.sortable = sortable
        self.sort_by = sort_by
        self.searchable = searchable
        self.search_in = search_in
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
