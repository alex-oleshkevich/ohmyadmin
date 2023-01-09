import functools
import typing

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette_babel import gettext_lazy as _
from starlette_flash import flash

from ohmyadmin.datasource.base import DataSource
from ohmyadmin.ordering import get_ordering_value
from ohmyadmin.pages.base import BasePage
from ohmyadmin.pagination import get_page_size_value, get_page_value, Page
from ohmyadmin.views.base import IndexView
from ohmyadmin.views.table import TableView


def get_search_value(request: Request, param_name: str) -> str:
    return request.query_params.get(param_name, '').strip()


class Resource(BasePage, Router):
    group = _('Resources', domain='ohmyadmin')
    index_view_class: type[IndexView] = TableView
    datasource: DataSource
    page_param: typing.ClassVar[str] = 'page'
    page_size_param: typing.ClassVar[str] = 'page_size'
    search_param: typing.ClassVar[str] = 'search'
    ordering_param: typing.ClassVar[str] = 'ordering'
    page_size: typing.ClassVar[int] = 25
    max_page_size: typing.ClassVar[int] = 100

    def __init__(self) -> None:
        super().__init__(routes=self.get_routes())

    async def index_view(self, request: Request) -> Response:
        page_number = get_page_value(request, self.page_param)
        page_size = get_page_size_value(request, self.page_size_param, self.max_page_size, self.page_size)
        search_term = get_search_value(request, self.search_param)
        ordering = get_ordering_value(request, self.ordering_param)

        # query = self.datasource.clone()
        # if search_term:
        #     query = query.apply_search(search_term)
        # if ordering:
        #     query = query.apply_ordering(ordering)
        # objects = await query.paginate(request, page=page_number, page_size=page_size)

        objects = Page([], 0, 1, 25)
        view = self.index_view_class()
        view_content = view.render(request, objects)
        context = {
            'resource': self,
            'objects': objects,
            'page_url': functools.partial(self.page_url, request),
            'view_content': view_content,
            'page_title': self.label_plural,
        }
        return self.render_to_response(request, 'ohmyadmin/resources/index.html', context)

    async def edit_view(self, request: Request) -> Response:
        pk = request.path_params.get('pk')
        if request.method == 'POST':
            flash(request).success('Submitted')
            return self.redirect_to_action(request, 'edit' if pk else 'create', pk=pk)

        context = {'resource': self, 'page_url': functools.partial(self.page_url, request)}
        if pk:
            return self.render_to_response(request, 'ohmyadmin/resources/edit.html', context)
        return self.render_to_response(request, 'ohmyadmin/resources/create.html', context)

    async def delete_view(self, request: Request) -> Response:
        request.path_params.get('pk')
        if request.method == 'POST':
            flash(request).success('Submitted')
            return self.redirect_to_action(request, 'index')

        context = {'page_url': functools.partial(self.page_url, request)}
        return self.render_to_response(request, 'ohmyadmin/resources/delete.html', context)

    def get_routes(self) -> list[BaseRoute]:
        return [
            Route('/', self.index_view, name=f'{self.get_path_name()}.index'),
            Route('/new', self.edit_view, name=f'{self.get_path_name()}.create', methods=['get', 'post']),
            Route('/{pk}/edit', self.edit_view, name=f'{self.get_path_name()}.edit', methods=['get', 'post']),
            Route('/{pk}/delete', self.delete_view, name=f'{self.get_path_name()}.delete', methods=['get', 'post']),
        ]

    def as_route(self) -> Mount:
        return Mount(f'/resources/{self.slug}', self)

    def page_url(self, request: Request, method: str, **path_params: typing.Any) -> str:
        return request.url_for(f'{self.get_path_name()}.{method}', **path_params)

    def redirect_to_action(self, request: Request, action: str, pk: typing.Any | None = None) -> RedirectResponse:
        path_params: dict[str, typing.Any] = {}
        if pk:
            path_params['pk'] = pk
        return self.redirect_to_path(request, f'{self.get_path_name()}.{action}', **path_params)

    @classmethod
    def generate_url(cls, request: Request) -> str:
        return request.url_for(f'{cls.get_path_name()}.index')

    @classmethod
    def get_path_name(cls) -> str:
        return f'ohmyadmin.resources.{cls.slug}'
