import dataclasses

import functools
import jinja2
import os
import pathlib
import time
import typing
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send

from ohmyadmin.flash import FlashMiddleware, flash
from ohmyadmin.i18n import _
from ohmyadmin.media_server import MediaServer
from ohmyadmin.nav import MenuGroup, MenuItem
from ohmyadmin.resources import Resource
from ohmyadmin.responses import Response
from ohmyadmin.storage import FileStorage
from ohmyadmin.templating import DynamicChoiceLoader, jinja_env

this_dir = pathlib.Path(__file__).parent


@dataclasses.dataclass
class UserMenu:
    user_name: str = 'Anonymous'
    avatar: str = ''
    menu: list[MenuItem | MenuGroup] = dataclasses.field(default_factory=list)


async def index_view(request: Request) -> Response:
    return request.state.admin.render_to_response(request, 'ohmyadmin/index.html')


class OhMyAdmin(Router):
    def __init__(
        self,
        resources: typing.Iterable[Resource],
        routes: list[BaseRoute] | None = None,
        template_dir: str | os.PathLike | None = None,
        file_storage: FileStorage | None = None,
        middleware: typing.Sequence[Middleware] | None = None,
    ) -> None:
        self.file_storage = file_storage
        self.resources = resources
        self.middleware = list(middleware or [])
        self.middleware.append(Middleware(FlashMiddleware))

        self.jinja_env = jinja_env
        self.jinja_env.globals.update({'admin': self})
        if template_dir:
            typing.cast(DynamicChoiceLoader, self.jinja_env.loader).add_loader(jinja2.FileSystemLoader([template_dir]))

        super().__init__(
            routes=[
                *(routes or []),
                *(self.get_routes()),
            ]
        )

    def build_main_menu(self, request: Request) -> typing.Iterable[MenuItem]:
        yield MenuGroup(
            text=_('Resources'), items=[MenuItem.to_resource(resource.__class__) for resource in self.resources]
        )

    def build_user_menu(self, request: Request) -> UserMenu:
        return UserMenu(user_name='anon.')

    def url_for(self, request: Request, path_name: str, **path_params: typing.Any) -> str:
        return request.url_for(path_name, **path_params)

    def static_url(self, request: Request, path: str) -> str:
        return self.url_for(request, 'static', path=path) + f'?{time.time()}'

    def render(self, template_name: str, context: typing.Mapping | None = None) -> str:
        template = self.jinja_env.get_template(template_name)
        return template.render(context or {})

    def render_to_response(
        self,
        request: Request,
        template_name: str,
        context: typing.Mapping | None = None,
        status_code: int = 200,
    ) -> Response:
        context = dict(context or {})
        context.update(
            {
                'request': request,
                'url': request.url_for,
                'main_menu': list(self.build_main_menu(request)),
                'user_menu': self.build_user_menu(request),
                'static': functools.partial(self.static_url, request),
                'flash_messages': flash(request),
            }
        )
        content = self.render(template_name, context)
        return Response(content, status_code=status_code, media_type='text/html')

    def get_routes(self) -> typing.Iterable[BaseRoute]:
        yield Route('/', index_view, name='ohmyadmin_welcome')
        yield Mount('/static', StaticFiles(packages=[__name__.split('.')[0]]), name='static')

        if self.file_storage:
            yield Mount('/media', MediaServer(self.file_storage), name='media')

        for resource in self.resources:
            yield Mount(f'/resources/{resource.id}', resource)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        from ohmyadmin.globals import globalize_admin

        with globalize_admin(self):
            scope.setdefault('state', {})
            scope['state']['admin'] = self
            scope['state']['file_storage'] = self.file_storage
            app = super().__call__
            for middleware in reversed(self.middleware):
                app = middleware.cls(app, **middleware.options)

            await app(scope, receive, send)
