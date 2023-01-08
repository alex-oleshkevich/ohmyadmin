from __future__ import annotations

import abc
import typing
from starlette.datastructures import URL
from starlette.requests import Request

from ohmyadmin.shortcuts import render_to_string


class MenuItem:
    def __init__(self, text: str, icon: str = '') -> None:
        self.text = text
        self.icon = icon

    def is_active(self, request: Request) -> bool:
        return False

    @abc.abstractmethod
    def render(self, request: Request) -> str:
        ...


class MenuLink(MenuItem):
    def __init__(self, text: str, url: str | URL, icon: str = '') -> None:
        super().__init__(text=text, icon=icon)
        self.url = str(url)

    def is_active(self, request: Request) -> bool:
        return str(request.url).startswith(self.url)

    def render(self, request: Request) -> str:
        return render_to_string(
            request,
            'ohmyadmin/menu_item_link.html',
            {
                'item': self,
                'is_active': self.is_active(request),
            },
        )


class MenuGroup(MenuItem):
    def __init__(self, text: str, items: list[MenuItem], icon: str = '') -> None:
        super().__init__(text=text, icon=icon)
        self.items = items

    def __iter__(self) -> typing.Iterator[MenuItem]:
        yield from self.items

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/menu_group.html', {'group': self})
