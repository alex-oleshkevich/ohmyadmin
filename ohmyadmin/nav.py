from __future__ import annotations

import abc
import typing
from starlette.requests import Request

from ohmyadmin.helpers import render_to_string

if typing.TYPE_CHECKING:
    from ohmyadmin.resources import Resource


class MenuItem(abc.ABC):
    template: str = ''

    def __init__(self, text: str, icon: str = '') -> None:
        self.text = text
        self.icon = icon

    def render(self, request: Request) -> str:
        assert self.template
        return render_to_string(self.template, {'request': request, 'item': self})

    @classmethod
    def to_url(cls, text: str, url: str, icon: str = '') -> Link:
        return Link(text=text, url=url, icon=icon)

    @classmethod
    def to_route(
        cls,
        text: str,
        path_name: str,
        icon: str = '',
        path_params: dict[str, str | int] | None = None,
    ) -> RouteLink:
        return RouteLink(text=text, path_name=path_name, path_params=path_params or {}, icon=icon)

    @classmethod
    def to_resource(cls, resource: typing.Type[Resource]) -> RouteLink:
        return cls.to_route(resource.label_plural, resource.get_route_name('list'), resource.icon)

    __call__ = render


class MenuGroup(MenuItem):
    template: str = 'ohmyadmin/nav/menu_group.html'

    def __init__(self, text: str, items: list[MenuItem]) -> None:
        self.items = items
        super().__init__(text=text)

    def __iter__(self) -> typing.Iterator[MenuItem]:
        return iter(self.items)


class BaseLinkItem(MenuItem):
    template: str = 'ohmyadmin/nav/menu_item.html'

    @abc.abstractmethod
    def resolve(self, request: Request) -> str:
        ...

    def render(self, request: Request) -> str:
        return render_to_string(self.template, {'request': request, 'item': self, 'url': self.resolve(request)})


class Link(BaseLinkItem):
    def __init__(self, text: str, url: str, icon: str = '') -> None:
        self.url = url
        super().__init__(text=text, icon=icon)

    def resolve(self, request: Request) -> str:
        return self.url


class RouteLink(BaseLinkItem):
    def __init__(
        self,
        text: str,
        path_name: str,
        path_params: dict[str, int | str] | None = None,
        icon: str = '',
    ) -> None:
        self.path_name = path_name
        self.path_params = path_params or {}
        super().__init__(text=text, icon=icon)

    def resolve(self, request: Request) -> str:
        return request.url_for(self.path_name, **self.path_params)


class ResourceLink(BaseLinkItem):
    def __init__(self, resource: typing.Type[Resource]) -> None:
        self.resource = resource
        super().__init__(resource.label_plural, resource.icon)

    def resolve(self, request: Request) -> str:
        return request.url_for(self.resource.get_route_name('list'))
