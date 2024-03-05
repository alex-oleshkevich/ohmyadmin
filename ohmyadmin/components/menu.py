from __future__ import annotations

import typing

from starlette.datastructures import URL
from starlette.requests import Request

from ohmyadmin.components.base import Component
from ohmyadmin.routing import LazyURL


class MenuItem(Component):
    template_name = "ohmyadmin/components/menu/menu_item.html"

    def __init__(
        self,
        url: str | URL | LazyURL,
        label: str,
        icon: str = "",
        trailing: Component | None = None,
    ) -> None:
        self.url = URL(url) if isinstance(str, URL) else url
        self.label = label
        self.icon = icon
        self.trailing = trailing

    def resolve_url(self, request: Request) -> URL:
        match self.url:
            case URL():
                return self.url
            case LazyURL():
                return self.url.resolve(request)
            case _:
                return URL(self.url)

    def is_active(self, request: Request) -> bool:
        url = self.resolve_url(request)
        return request.url.path.startswith(url.path)


class MenuHeading(Component):
    template_name = "ohmyadmin/components/menu/menu_heading.html"

    def __init__(self, label: str) -> None:
        self.label = label


class MenuGroup(Component):
    template_name = "ohmyadmin/components/menu/menu.html"

    def __init__(self, items: typing.Sequence[Component], heading: str = "") -> None:
        self.heading = heading
        self.items = list(items)


class MenuBuilder(Component):
    """MenuBuilder dynamically creates menu items basing on the request data."""

    def __init__(self, builder: typing.Callable[[Request], Component]) -> None:
        self.builder = builder

    def render(self, request: Request) -> str:
        return self.builder(request).render(request)
