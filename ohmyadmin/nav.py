from __future__ import annotations

import dataclasses

import abc
import typing
from starlette.requests import Request

if typing.TYPE_CHECKING:
    from ohmyadmin.resources import Resource


class MenuItem(abc.ABC):
    @abc.abstractmethod
    def render_to_url(self, request: Request) -> str:
        raise NotImplementedError()

    @classmethod
    def to_url(cls, text: str, url: str, icon: str = '') -> Link:
        return Link(text=text, href=url, icon=icon)

    @classmethod
    def to_route(
        cls,
        text: str,
        path_name: str,
        icon: str = '',
        path_params: dict[str, str | int] | None = None,
    ) -> RouteLink:
        return RouteLink(text=text, path_name=path_name, path_params=path_params or {}, icon=icon)


@dataclasses.dataclass
class Link(MenuItem):
    text: str
    href: str
    icon: str = ''

    def render_to_url(self, request: Request) -> str:
        return self.href


@dataclasses.dataclass
class RouteLink(MenuItem):
    text: str
    path_name: str
    icon: str = ''
    path_params: dict[str, int | str] = dataclasses.field(default_factory=dict)

    def render_to_url(self, request: Request) -> str:
        return request.url_for(self.path_name, **self.path_params)


class ResourceLink(MenuItem):
    def __init__(self, resource: typing.Type[Resource]) -> None:
        self.resource = resource

    def render_to_url(self, request: Request) -> str:
        return request.url_for(self.resource.get_route_name('list'))


class MenuGroup:
    def __init__(self, label: str, items: list[MenuItem]) -> None:
        self.label = label
        self.items = items

    def __iter__(self) -> typing.Iterator[MenuItem]:
        return iter(self.items)
