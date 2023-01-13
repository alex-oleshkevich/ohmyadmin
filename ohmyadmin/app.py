import functools
import itertools
import jinja2
import operator
import os
import time
import typing
from async_storages import FileStorage, LocalStorage
from async_storages.file_server import FileServer
from markupsafe import Markup
from starlette import templating
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send
from starlette_babel import gettext_lazy as _
from starlette_babel.contrib.jinja import configure_jinja_env
from starlette_flash import flash
from tabler_icons import tabler_icon

from ohmyadmin.authentication import AdminUser, AnonymousAuthPolicy, BaseAuthPolicy
from ohmyadmin.menu import MenuGroup, MenuLink, NavItem
from ohmyadmin.pages.base import BasePage

START_TIME = time.time()
PACKAGE_NAME = __name__.split('.')[0]


class OhMyAdmin(Router):
    def __init__(
        self,
        title: str = 'Oh My Admin!',
        logo_url: str = '',
        pages: typing.Sequence[BasePage] | None = None,
        template_dir: str | os.PathLike | None = None,
        file_storage: FileStorage | None = None,
        user_menu: typing.Sequence[NavItem] | None = None,
        auth_policy: BaseAuthPolicy = AnonymousAuthPolicy(),
    ) -> None:
        self.title = title
        self.pages = pages or []
        self.logo_url = logo_url
        self.auth_policy = auth_policy
        self.user_menu = user_menu or []
        self.file_storage = file_storage or FileStorage(LocalStorage('/tmp/ohmyadmin', mkdirs=True))
        self.middleware: list[Middleware] = [
            Middleware(AuthenticationMiddleware, backend=auth_policy.get_authentication_backend()),
        ]

        self.jinja_env = jinja2.Environment(
            autoescape=True,
            loader=jinja2.ChoiceLoader(
                [jinja2.FileSystemLoader(template_dir or '__undefined__'), jinja2.PackageLoader(PACKAGE_NAME)]
            ),
        )
        self.jinja_env.globals.update(
            {
                'admin': self,
                'tabler_icon': tabler_icon,
            }
        )
        configure_jinja_env(self.jinja_env)

        self.templates = templating.Jinja2Templates('')
        self.templates.env = self.jinja_env

        super().__init__(self.get_routes())

    def url_for(self, request: Request, path_name: str, **path_params: typing.Any) -> str:
        return request.url_for(path_name, **path_params)

    def static_url(self, request: Request, path: str) -> str:
        _suffix = time.time() if request.app.debug else START_TIME
        return request.url_for('ohmyadmin.static', path=path) + f'?{_suffix}'

    def media_url(self, request: Request, path: str) -> str:
        if path.startswith('http://') or path.startswith('https://'):
            return path
        return request.url_for('ohmyadmin.media', path=path)

    def render_to_string(
        self,
        request: Request,
        template_name: str,
        context: typing.Mapping[str, typing.Any] | None = None,
    ) -> str:
        context = dict(context or {})
        context.update(
            {
                'request': request,
                'url': functools.partial(self.url_for, request),
                'static_url': functools.partial(self.static_url, request),
                'media_url': functools.partial(self.media_url, request),
                'flash_messages': flash(request),
            }
        )
        return Markup(self.templates.get_template(template_name).render(context))

    def render_macro(self, template_name: str, macro_name: str, macro_args: dict[str, typing.Any] | None = None) -> str:
        macro_args = macro_args or {}
        template = self.templates.get_template(template_name)
        macros = getattr(template.module, macro_name)
        return macros(**macro_args)

    def render_to_response(
        self,
        request: Request,
        template_name: str,
        context: typing.Mapping[str, typing.Any] | None = None,
        headers: typing.Mapping[str, typing.Any] | None = None,
    ) -> Response:
        context = dict(context or {})
        context.update(
            {
                'request': request,
                'url': functools.partial(self.url_for, request),
                'static_url': functools.partial(self.static_url, request),
                'media_url': functools.partial(self.media_url, request),
                'flash_messages': flash(request),
            }
        )
        return self.templates.TemplateResponse(template_name, context, headers=headers)

    def get_routes(self) -> typing.Sequence[BaseRoute]:
        return [
            Route('/', self.index_view, name='ohmyadmin.welcome'),
            Route('/login', self.login_view, name='ohmyadmin.login', methods=['GET', 'POST']),
            Route('/logout', self.logout_view, name='ohmyadmin.logout', methods=['POST']),
            Mount('/static', StaticFiles(packages=['ohmyadmin']), name='ohmyadmin.static'),
            Mount('/media', FileServer(self.file_storage), name='ohmyadmin.media'),
            *[page.as_route() for page in self.pages],
        ]

    def index_view(self, request: Request) -> Response:
        return self.render_to_response(
            request, 'ohmyadmin/index.html', {'page_title': _('Welcome', domain='ohmyadmin')}
        )

    async def login_view(self, request: Request) -> Response:
        next_url = request.query_params.get('next', request.url_for('ohmyadmin.welcome'))
        form_class = self.auth_policy.get_login_form_class()
        form = form_class(formdata=await request.form(), data={'next_url': next_url})
        if request.method in ['POST'] and form.validate():
            if user := await self.auth_policy.authenticate(request, form.identity.data, form.password.data):
                self.auth_policy.login(request, user)
                flash(request).success(_('You have been logged in.', domain='ohmyadmin'))
                return RedirectResponse(url=form.next_url.data, status_code=302)
            else:
                flash(request).error(_('Invalid credentials.', domain='ohmyadmin'))

        return self.render_to_response(
            request,
            'ohmyadmin/login.html',
            {
                'request': request,
                'form': form,
                'next_url': next_url,
                'page_title': _('Login', domain='ohmyadmin'),
            },
        )

    async def logout_view(self, request: Request) -> Response:
        self.auth_policy.logout(request)
        flash(request).success(_('You have been logged out.', domain='ohmyadmin'))
        return RedirectResponse(request.url_for('ohmyadmin.login'), status_code=302)

    def get_current_user(self, request: Request) -> AdminUser:
        return request.user

    def get_user_menu(self, request: Request) -> typing.Sequence[NavItem]:
        user_menu = self.user_menu
        return user_menu

    def get_main_menu(self, request: Request) -> list[NavItem]:
        groups = itertools.groupby(
            self.pages,
            key=operator.attrgetter('group'),
        )
        return [
            MenuGroup(
                text=group[0],
                items=[
                    MenuLink(
                        icon=item.icon,
                        text=item.label_plural,
                        url=item.generate_url(request),
                    )
                    for item in group[1]
                ],
            )
            for group in groups
        ]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope.setdefault('state', {})
        scope['state'].update({'admin': self})

        app = super().__call__
        for middleware in reversed(self.middleware):
            app = middleware.cls(app, **middleware.options)

        await app(scope, receive, send)
