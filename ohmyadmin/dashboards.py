from __future__ import annotations

import anyio
import typing
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route

from ohmyadmin.menus import MenuItem
from ohmyadmin.metrics import Metric, RenderedMetric

if typing.TYPE_CHECKING:
    from ohmyadmin.admin import OhMyAdmin


class Dashboard:
    slug: str = ''
    icon: str = ''
    title: str = ''
    metrics: list[typing.Type[Metric]] | None = None

    def __init__(self, admin: OhMyAdmin) -> None:
        self.admin = admin
        self.metrics = list(self.metrics or [])
        if not self.title:
            self.title = self.__class__.__name__.replace('_', ' ').removesuffix('Dashboard').title()

    def get_route(self) -> BaseRoute:
        return Route('/' + self.slug, self.index_view, name=self.slug)

    def get_menu_item(self) -> MenuItem:
        return MenuItem(label=self.title, path_name=self.slug, icon=self.icon)

    def get_metrics(self) -> list[Metric]:
        return [metric_class() for metric_class in self.metrics or []]

    async def index_view(self, request: Request) -> Response:
        rendered: list[RenderedMetric] = []

        async def _render(metric: Metric) -> None:
            rendered.append(RenderedMetric(metric, await metric.render(request)))

        async with anyio.create_task_group() as tg:
            for metric in self.get_metrics():
                tg.start_soon(_render, metric)

        return self.admin.render_to_response(
            request,
            'ohmyadmin/dashboard.html',
            {
                'dashboard': self,
                'metrics': rendered,
            },
        )
