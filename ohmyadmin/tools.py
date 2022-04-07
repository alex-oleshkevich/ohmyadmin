from __future__ import annotations

import inspect
import os
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount

from ohmyadmin.admin import OhMyAdmin
from ohmyadmin.menus import MenuItem
from ohmyadmin.request import AdminRequest
from ohmyadmin.routing import Route


class Tool:
    __abstract__ = True
    slug: str = ''
    title: str = ''
    icon: str = ''
    template_dir: str | os.PathLike = ''

    def __init__(self, admin: OhMyAdmin) -> None:
        self.admin = admin
        if not self.title:
            self.title = self.__class__.__name__.replace('_', ' ').title()

        self.routes = [Route('/', self.index_view, name=self.slug)]
        for name, member in inspect.getmembers(self, inspect.ismethod):
            if spec := getattr(member, '__route_spec__', None):
                self.routes.append(Route(spec.path, member, methods=spec.methods, name=spec.name or name))

    def get_route(self) -> BaseRoute:
        return Mount('/' + self.slug, routes=self.routes)

    def get_menu_item(self, request: AdminRequest) -> MenuItem:
        return MenuItem(label=self.title, path_name=self.slug, icon=self.icon)

    async def index_view(self, request: AdminRequest) -> Response:
        return self.admin.render_to_response(request, 'ohmyadmin/tool_stub.html')
