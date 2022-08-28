import typing
from starlette.requests import Request


class MenuItem:
    def __init__(
        self,
        label: str,
        *,
        url: str | None = None,
        icon: str = '',
        external: bool = False,
        path_name: str | None = None,
        path_params: dict[str, typing.Any] | None = None,
    ) -> None:
        assert url or path_name, 'Either "url" or "path_name" argument expected.'
        self.label = label
        self._url = url
        self.path_name = path_name
        self.path_params = path_params or {}
        self.icon = icon
        self.external = external

    def url(self, request: Request) -> str:
        if self._url:
            return self._url
        assert self.path_name
        return request.scope['router'].url_path_for(self.path_name, **self.path_params)

    def is_active(self, request: Request) -> bool:
        return self.url(request) in request.url.path

    def render(self, request: Request) -> str:
        return request.state.admin.render('ohmyadmin/menu_item.html', {'request': request, 'menu_item': self})

    def __str__(self) -> str:
        return self.label


class MenuGroup:
    def __init__(self, label: str, items: list[MenuItem], collapsible: bool = False, icon: str = '') -> None:
        self.label = label
        self.collapsible = collapsible
        self.icon = icon
        self.items = items or []

    def is_open(self, request: Request) -> bool:
        return any([item.is_active(request) for item in self.items])

    def render(self, request: Request) -> str:
        return request.state.admin.render('ohmyadmin/menu_group.html', {'request': request, 'group': self})

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
