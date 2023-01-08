import functools
import typing
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette_babel import gettext_lazy as _
from starlette_flash import flash

from ohmyadmin.page import BasePage


class Resource(BasePage, Router):
    group = _('Resources', domain='ohmyadmin')

    def __init__(self) -> None:
        super().__init__(routes=self.get_routes())

    def page_url(self, request: Request, method: str, **path_params: typing.Any) -> str:
        return request.url_for(f'{self.get_path_name()}.{method}', **path_params)

    def redirect_to_action(self, request: Request, action: str, pk: typing.Any | None = None) -> RedirectResponse:
        path_params: dict[str, typing.Any] = {}
        if pk:
            path_params['pk'] = pk
        return self.redirect_to_path(request, f'{self.get_path_name()}.{action}', **path_params)

    async def index_view(self, request: Request) -> Response:
        context = {'page_url': functools.partial(self.page_url, request)}
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

    @classmethod
    def get_path_name(cls) -> str:
        return f'ohmyadmin.resources.{cls.slug}'

    def as_route(self) -> Mount:
        return Mount(f'/resources/{self.slug}', self)

    @classmethod
    def generate_url(cls, request: Request) -> str:
        return request.url_for(f'{cls.get_path_name()}.index')
