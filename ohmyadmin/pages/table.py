from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route

from ohmyadmin.pages.page import Page
from ohmyadmin.pages.pagemixins import IndexViewMixin


class TablePage(IndexViewMixin, Page):
    __abstract__ = True

    async def get(self, request: Request) -> Response:
        return await self.dispatch_index_view(request)

    async def handler(self, request: Request) -> Response:
        request.state.datasource = self.datasource
        return await super().handler(request)

    def as_route(self) -> BaseRoute:
        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        return Route(f'/{self.slug}', self, methods=methods, name=self.get_path_name())
