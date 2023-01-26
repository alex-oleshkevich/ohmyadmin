from __future__ import annotations

import abc
import typing
from starlette.datastructures import URL
from starlette.requests import Request

from ohmyadmin.helpers import LazyURL, resolve_url
from ohmyadmin.shortcuts import render_to_string


class NavItem(abc.ABC):  # pragma: no cover
    @abc.abstractmethod
    def is_active(self, request: Request) -> bool:
        ...

    @abc.abstractmethod
    def render(self, request: Request) -> str:
        ...


class MenuLink(NavItem):
    """
    Menu item for use in primary navigation (e.

    g. in a sidebar).
    """

    def __init__(self, text: str, url: str | LazyURL, icon: str = '') -> None:
        self.text = text
        self.icon = icon
        self.url = url

    def is_active(self, request: Request) -> bool:
        return request.url.path.startswith(resolve_url(request, self.url).path)

    def resolve(self, request: Request) -> URL:
        return resolve_url(request, self.url)

    def render(self, request: Request) -> str:
        return render_to_string(
            request,
            'ohmyadmin/menu_item_link.html',
            {
                'item': self,
                'is_active': self.is_active(request),
            },
        )


class MenuGroup(NavItem):
    def __init__(self, text: str, items: list[MenuLink], icon: str = '') -> None:
        self.text = text
        self.icon = icon
        self.items = items

    def __iter__(self) -> typing.Iterator[MenuLink]:
        yield from self.items

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/menu_group.html', {'group': self})

    def is_active(self, request: Request) -> bool:
        return any([item.is_active(request) for item in self.items])
