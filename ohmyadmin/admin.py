import jinja2
import time
import typing
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette.staticfiles import StaticFiles
from tabler_icons import tabler_icon

from ohmyadmin.menus import MenuGroup, MenuItem, UserMenu
from ohmyadmin.request import AdminRequest


class OhMyAdmin(Router):
    def __init__(
        self,
        template_paths: list[str] | None = None,
        app_name: str = 'oma',
        user_menu_config: typing.Callable[[AdminRequest, UserMenu], None] | None = None,
    ) -> None:
        self.app_name = app_name
        self.user_menu_config = user_menu_config or self._default_user_menu_config
        self.jinja_env = jinja2.Environment(
            extensions=['jinja2.ext.i18n', 'jinja2.ext.debug'],
            loader=jinja2.ChoiceLoader(
                [
                    jinja2.loaders.PackageLoader('ohmyadmin'),
                    jinja2.loaders.FileSystemLoader(template_paths or []),
                ]
            ),
        )
        self.jinja_env.globals.update(
            {
                'admin': self,
                'static': self.static_url,
                'url': self.url_for,
                'icon': tabler_icon,
            }
        )

        self.bootstrap()
        super().__init__(routes=self.get_routes())

    def get_routes(self) -> list[BaseRoute]:
        return [
            Route('/', self.welcome_view, name='welcome'),
            Route('/logout', self.logout_view, name='logout'),
            Mount('/static', StaticFiles(packages=['ohmyadmin']), name='static'),
        ]

    @property
    def main_menu(self) -> list[MenuItem | MenuGroup]:
        return [
            MenuItem('Overview', '/admin', icon='dashboard'),
            MenuGroup(
                'Resources',
                [
                    MenuItem('Users', '/admin/users', icon='user'),
                    MenuItem('Groups', '/admin/groups', icon='users'),
                    MenuItem('Species', '/admin/species', icon='feather'),
                    MenuItem('Read more', '/admin/read-more', external=True),
                ],
                collapsible=True,
                icon='bucket',
            ),
            MenuItem('Families', '/admin/families'),
            MenuItem('Orders', '/admin/orders', external=True),
        ]

    def _default_user_menu_config(self, request: AdminRequest, user_menu: UserMenu) -> None:
        user_menu.name = getattr(request.user, 'display_name', '<user>')
        user_menu.photo = getattr(request.user, 'avatar', '')

    def get_user_menu(self, request: AdminRequest) -> UserMenu:
        user_menu = UserMenu(name='<anon.>', items=[], photo='')
        self.user_menu_config(request, user_menu)
        user_menu.items.append(MenuItem('Log out', self.url_for(request, 'logout')))
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
        path_name = self.path_name(path_name)
        return request.url_for(path_name, **path_params)

    def static_url(self, request: AdminRequest, path: str) -> str:
        return self.url_for(request, 'static', path=path) + f'?{time.time()}'

    def welcome_view(self, request: Request) -> Response:
        request = AdminRequest.from_starlette(request, self)
        return self.render_to_response(request, 'index.html')

    def path_name(self, path_name: str) -> str:
        return f'{self.app_name}:{path_name}'

    async def logout_view(self, request: Request) -> Response:
        return Response('')
