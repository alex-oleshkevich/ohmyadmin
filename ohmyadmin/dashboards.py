from __future__ import annotations

import typing
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route

from ohmyadmin.menus import MenuItem
from ohmyadmin.metrics import Metric

if typing.TYPE_CHECKING:
    from ohmyadmin.admin import OhMyAdmin


class Dashboard:
    slug: str = ''
    icon: str = ''
    title: str = ''
    metrics: list[Metric]

    def __init__(self, admin: OhMyAdmin) -> None:
        self.admin = admin
        if not self.title:
            self.title = self.__class__.__name__.replace('_', ' ').removesuffix('Dashboard').title()

    def get_route(self) -> BaseRoute:
        return Route('/' + self.slug, self.index_view, name=self.slug)

    def get_menu_item(self) -> MenuItem:
        return MenuItem(label=self.title, path_name=self.slug, icon=self.icon)

    async def index_view(self, request: Request) -> Response:
        return self.admin.render_to_response(request, 'ohmyadmin/dashboard.html')
