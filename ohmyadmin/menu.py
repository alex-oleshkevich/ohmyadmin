from __future__ import annotations

import abc
import typing
from starlette.datastructures import URL
from starlette.requests import Request

from ohmyadmin.templating import macro


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
        macros = macro('ohmyadmin/menu.html', 'menu_link')
        return macros(url=self.url, text=self.text, icon=self.icon, is_active=self.is_active(request))


class MenuGroup(MenuItem):
    def __init__(self, text: str, items: list[MenuItem], icon: str = '') -> None:
        super().__init__(text=text, icon=icon)
        self.items = items

    def __iter__(self) -> typing.Iterator[MenuItem]:
        yield from self.items

    def render(self, request: Request) -> str:
        macros = macro('ohmyadmin/menu.html', 'menu_group')
        return macros(request=request, text=self.text, icon=self.icon, items=self.items)
