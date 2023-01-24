from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route

from ohmyadmin.pages.page import TemplatePage
from ohmyadmin.pages.pagemixins import IndexViewMixin


class TablePage(IndexViewMixin, TemplatePage):
    __abstract__ = True

    async def get(self, request: Request) -> Response:
        return await self.dispatch_index_view(request)

    def as_route(self) -> BaseRoute:
        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        return Mount(
            f'/{self.slug}',
            routes=[
                Route('/', self.dispatch_index_view, methods=methods, name=self.get_path_name()),
            ],
        )
