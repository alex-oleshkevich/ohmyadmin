from __future__ import annotations

import jinja2
import os
import time
import typing
from slugify import slugify
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send
from tabler_icons import tabler_icon

from ohmyadmin.dashboards import Dashboard
from ohmyadmin.menus import MenuGroup, MenuItem, UserMenu
from ohmyadmin.request import AdminRequest

if typing.TYPE_CHECKING:
    from ohmyadmin.tools import Tool

T = typing.TypeVar('T')


def ensure_slug(obj: typing.Type[T]) -> typing.Type[T]:
    slug = getattr(obj, 'slug', '')
    if not slug:
        setattr(obj, 'slug', slugify(obj.__name__))
    return obj


class OhMyAdmin(Router):
    def __init__(
        self,
        template_dirs: list[str | os.PathLike] | None = None,
        app_name: str = 'oma',
        user_menu_config: typing.Callable[[AdminRequest, UserMenu], None] | None = None,
        dashboards: list[typing.Type[Dashboard]] | None = None,
        tools: list[typing.Type[Tool]] | None = None,
    ) -> None:
        self.app_name = app_name
        self.template_dirs = template_dirs or []
        self.user_menu_config = user_menu_config or self._default_user_menu_config

        # setup dashboards
        self.dashboards = [ensure_slug(dashboard)(self) for dashboard in dashboards or []]

        # setup tools
        self.tools: list[Tool] = []
        for tool in tools or []:
            if not tool.slug:
                tool.slug = slugify(tool.__name__)
            if tool.template_dir:
                self.template_dirs.append(tool.template_dir)
            self.tools.append(tool(self))

        self.jinja_env = self._create_jinja_env()
        self.bootstrap()
        super().__init__(routes=self.get_routes())

    def get_routes(self) -> list[BaseRoute]:
        return [
            Route('/', self.welcome_view, name='welcome'),
            Route('/logout', self.logout_view, name='logout'),
            Mount('/static', StaticFiles(packages=['ohmyadmin']), name='static'),
            *self.get_tool_routes(),
            *self.get_dashboard_routes(),
        ]

    def get_tool_routes(self) -> list[BaseRoute]:
        mounts = []
        for tool in self.tools:
            mounts.append(tool.get_route())
        return mounts

    def get_dashboard_routes(self) -> list[BaseRoute]:
        return [dashboard.get_route() for dashboard in self.dashboards]

    def get_main_menu(self, request: AdminRequest) -> list[MenuItem | MenuGroup]:
        dashboard_menus: list[MenuItem | MenuGroup] = []
        resource_menus: list[MenuItem | MenuGroup] = []
        tool_menus: list[MenuItem | MenuGroup] = []
        for tool in self.tools:
            tool_menus.append(tool.get_menu_item())

        for dashboard in self.dashboards:
            dashboard_menus.append(dashboard.get_menu_item())

        return [
            *dashboard_menus,
            *resource_menus,
            *tool_menus,
        ]

    def _default_user_menu_config(self, request: AdminRequest, user_menu: UserMenu) -> None:
        user_menu.name = getattr(request.user, 'display_name', '<user>')
        user_menu.photo = getattr(request.user, 'avatar', '')

    def get_user_menu(self, request: AdminRequest) -> UserMenu:
        user_menu = UserMenu(name='<anon.>', items=[], photo='')
        self.user_menu_config(request, user_menu)
        user_menu.items.append(MenuItem('Log out', path_name='logout'))
        return user_menu

    def bootstrap(self) -> None:
        ...

    def render(self, template_name: str, context: dict[str, typing.Any] | None = None) -> str:
        template = self.jinja_env.get_template(template_name)
        return template.render(context or {})

    def render_to_response(
        self,
        request: AdminRequest,
        template_name: str,
        context: dict[str, typing.Any] | None = None,
        status_code: int = 200,
    ) -> Response:
        context = context or {}
        context.update(
            {
                'request': request,
            }
        )
        content = self.render(template_name, context)
        return Response(content, status_code, media_type='text/html')

    def url_for(self, request: AdminRequest, path_name: str, **path_params: typing.Any) -> str:
        return request.url_for(path_name, **path_params)

    def static_url(self, request: AdminRequest, path: str) -> str:
        return self.url_for(request, 'static', path=path) + f'?{time.time()}'

    def welcome_view(self, request: Request) -> Response:
        request = AdminRequest.from_starlette(request)
        return self.render_to_response(request, 'ohmyadmin/index.html')

    async def logout_view(self, request: Request) -> Response:
        return Response('')

    def _create_jinja_env(self) -> jinja2.Environment:
        jinja_env = jinja2.Environment(
            extensions=['jinja2.ext.i18n', 'jinja2.ext.debug'],
            loader=jinja2.ChoiceLoader(
                [
                    jinja2.loaders.PackageLoader('ohmyadmin'),
                    jinja2.loaders.FileSystemLoader(self.template_dirs or []),
                ]
            ),
        )
        jinja_env.globals.update(
            {
                'admin': self,
                'static': self.static_url,
                'url': self.url_for,
                'icon': tabler_icon,
            }
        )
        return jinja_env

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope['ohmyadmin'] = self
        return await super().__call__(scope, receive, send)
