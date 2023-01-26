from starlette.routing import BaseRoute, Mount, Route

from ohmyadmin.pages.page import Page
from ohmyadmin.pages.pagemixins import IndexViewMixin


class TablePage(IndexViewMixin, Page):
    """Table pages display lists of objects with option to sort, search, and filter."""

    __abstract__ = True

    def as_route(self) -> BaseRoute:
        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        return Mount(
            f'/{self.slug}',
            routes=[
                Route('/', self.dispatch_index_view, methods=methods, name=self.get_path_name()),
            ],
        )
