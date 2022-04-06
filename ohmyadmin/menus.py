import typing

from ohmyadmin.request import AdminRequest


class MenuItem:
    def __init__(self, label: str, url: str, icon: str = '', external: bool = False) -> None:
        self.label = label
        self.url = url
        self.icon = icon
        self.external = external

    def is_active(self, request: AdminRequest) -> bool:
        return self.url in request.url.path

    def render(self, request: AdminRequest) -> str:
        return request.admin.render('menu_item.html', {'request': request, 'menu_item': self})

    def __str__(self) -> str:
        return self.label


class MenuGroup:
    def __init__(self, label: str, items: list[MenuItem], collapsible: bool = False, icon: str = '') -> None:
        self.label = label
        self.collapsible = collapsible
        self.icon = icon
        self.items = items or []

    def is_open(self, request: AdminRequest) -> bool:
        return any([item.is_active(request) for item in self.items])

    def render(self, request: AdminRequest) -> str:
        return request.admin.render('menu_group.html', {'request': request, 'group': self})

    def __str__(self) -> str:
        return self.label

    def __iter__(self) -> typing.Iterable[MenuItem]:
        return iter(self.items)


class UserMenu:
    def __init__(self, name: str, items: list[MenuItem], photo: str = '') -> None:
        self.name = name
        self.items = items
        self.photo = photo

    def __str__(self) -> str:
        return self.name

    def __iter__(self) -> typing.Iterable[MenuItem]:
        return iter(self.items)
