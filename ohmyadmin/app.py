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
from tabler_icons import tabler_icon

from ohmyadmin.helpers import dict_to_attrs
from ohmyadmin.nav import MenuGroup, MenuItem

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
        self.jinja_env = self._create_jinja_env(template_dirs or [])

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
                'static': functools.partial(self.static_url, request),
                'main_menu': self.build_main_menu(request),
                'user_menu': self.build_user_menu(request),
            }
        )
        content = self.render(template_name, context)
        return Response(content, status_code=status_code, media_type='text/html')

    def _create_jinja_env(self, template_dirs: list[str | os.PathLike]) -> jinja2.Environment:
        jinja_env = jinja2.Environment(
            extensions=['jinja2.ext.i18n', 'jinja2.ext.do'],
            loader=jinja2.ChoiceLoader(
                [
                    jinja2.loaders.FileSystemLoader(template_dirs),
                    jinja2.loaders.PackageLoader('ohmyadmin'),
                ]
            ),
        )
        jinja_env.globals.update(
            {
                'admin': self,
                'icon': tabler_icon,
                'tabler_icon': tabler_icon,
            }
        )
        jinja_env.tests.update(
            {
                'is_menu_group': lambda x: isinstance(x, MenuGroup),
            }
        )
        jinja_env.filters.update(
            {
                'dict_to_attrs': dict_to_attrs,
            }
        )
        jinja_env.install_null_translations()  # type: ignore
        return jinja_env

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope.setdefault('state', {})
        scope['state']['admin'] = self
        return await super().__call__(scope, receive, send)
