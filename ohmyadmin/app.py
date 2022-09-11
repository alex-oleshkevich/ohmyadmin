import dataclasses

import functools
import jinja2
import os
import pathlib
import time
import typing
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send

from ohmyadmin.flash import FlashMiddleware, flash
from ohmyadmin.nav import MenuGroup, MenuItem
from ohmyadmin.templating import jinja_env

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
        routes: list[BaseRoute] | None = None,
        template_dirs: list[str | os.PathLike] | None = None,
    ) -> None:
        self.jinja_env = jinja_env
        self.jinja_env.globals.update({'admin': self})
        self.jinja_env.loader.add_loader(jinja2.FileSystemLoader(template_dirs))

        super().__init__(
            routes=[
                Route('/', index_view, name='welcome'),
                Mount('/static', StaticFiles(directory=this_dir / 'statics'), name='static'),
                *(routes or []),
            ]
        )

    def build_main_menu(self, request: Request) -> list[MenuItem | MenuGroup]:
        return []

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
                'main_menu': self.build_main_menu(request),
                'user_menu': self.build_user_menu(request),
                'static': functools.partial(self.static_url, request),
                'flash_messages': flash(request),
            }
        )
        content = self.render(template_name, context)
        return Response(content, status_code=status_code, media_type='text/html')

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        from ohmyadmin.helpers import globalize_admin

        with globalize_admin(self):
            scope.setdefault('state', {})
            scope['state']['admin'] = self
            app = super().__call__
            app = FlashMiddleware(app)
            await app(scope, receive, send)
