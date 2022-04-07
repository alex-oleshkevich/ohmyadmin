from __future__ import annotations

import typing
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route

from ohmyadmin.menus import MenuItem

if typing.TYPE_CHECKING:
    from ohmyadmin.admin import OhMyAdmin


class Resource:
    slug: str = ''
    title: str = ''
    title_plural: str = ''
    icon: str = ''
    pk_type: str = 'int'

    def __init__(self, admin: OhMyAdmin) -> None:
        if not self.title:
            self.title = self.__class__.__name__.replace('_', ' ').removesuffix('Resource').title()
        self.admin = admin
        self.title_plural = self.title_plural or self.title + 's'

    def get_routes(self) -> list[BaseRoute]:
        return [
            Route(f'/{self.slug}', self.index_view, name=self.url_name('list')),
            Route(f'/{self.slug}/create', self.create_view, methods=['get', 'post'], name=self.url_name('create')),
            Route(
                f'/{self.slug}/{{id:}}/edit',
                self.create_view,
                methods=['get', 'post', 'put', 'patch'],
                name=self.url_name('edit'),
            ),
            Route(
                f'/{self.slug}/{{id:}}/delete',
                self.create_view,
                methods=['get', 'post', 'delete'],
                name=self.url_name('delete'),
            ),
        ]

    def get_menu_item(self) -> MenuItem:
        return MenuItem(label=self.title_plural, path_name=self.url_name('list'), icon=self.icon)

    async def index_view(self, request: Request) -> Response:
        return self.admin.render_to_response(
            request,
            'ohmyadmin/resource_list.html',
            {
                'request': request,
                'resource': self,
            },
        )

    async def create_view(self, request: Request) -> Response:
        return self.admin.render_to_response(
            request,
            'ohmyadmin/resource_create.html',
            {
                'request': request,
                'resource': self,
            },
        )

    async def update_view(self, request: Request) -> Response:
        return self.admin.render_to_response(
            request,
            'ohmyadmin/resource_edit.html',
            {
                'request': request,
                'resource': self,
            },
        )

    async def delete_view(self, request: Request) -> Response:
        return self.admin.render_to_response(
            request,
            'ohmyadmin/resource_delete.html',
            {
                'request': request,
                'resource': self,
            },
        )

    def url_name(self, action: str) -> str:
        return f'{self.slug}_{action}'
