import itertools
import jinja2
import operator
import os
import pathlib
import time
import typing
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send
from starlette_flash import flash

from ohmyadmin.auth import AnonymousAuthPolicy, BaseAuthPolicy, RequireLoginMiddleware, UserMenu
from ohmyadmin.dashboards import Dashboard
from ohmyadmin.globals import globalize_request
from ohmyadmin.i18n import _
from ohmyadmin.layout import FormElement, Grid
from ohmyadmin.media_server import MediaServer
from ohmyadmin.menu import MenuGroup, MenuItem, MenuLink
from ohmyadmin.pages import Page
from ohmyadmin.resources import Resource
from ohmyadmin.storage import FileStorage
from ohmyadmin.templating import DynamicChoiceLoader, TemplateResponse, admin_context, jinja_env

this_dir = pathlib.Path(__file__).parent


class OhMyAdmin(Router):
    def __init__(
        self,
        title: str = 'Oh My Admin!',
        logo_url: str = '',
        resources: typing.Iterable[Resource] | None = None,
        pages: typing.Iterable[Page] | None = None,
        dashboards: typing.Iterable[Dashboard] | None = None,
        routes: list[BaseRoute] | None = None,
        template_dir: str | os.PathLike | None = None,
        file_storage: FileStorage | None = None,
        auth_policy: BaseAuthPolicy | None = None,
        middleware: typing.Sequence[Middleware] | None = None,
    ) -> None:
        self.title = title
        self.logo_url = logo_url
        self.file_storage = file_storage
        self.pages = pages or []
        self.resources = resources or []
        self.dashboards = dashboards or []
        self.auth_policy = auth_policy or AnonymousAuthPolicy()
        self.middleware = list(middleware or [])
        self.middleware.extend(
            [
                Middleware(AuthenticationMiddleware, backend=self.auth_policy.get_authentication_backend()),
                Middleware(RequireLoginMiddleware, exclude_paths=['/login', '/logout', '/static', '/media']),
            ]
        )

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
        groups = itertools.groupby(
            [
                *self.dashboards,
                *self.resources,
                *self.pages,
            ],
            key=operator.attrgetter('group'),
        )
        for group in groups:
            yield MenuGroup(
                text=group[0],
                items=[
                    MenuLink(
                        text=getattr(item, 'label_plural', getattr(item, 'label')),
                        icon=getattr(item, 'icon', ''),
                        url=request.url_for(item.url_name()),  # type: ignore[attr-defined]
                    )
                    for item in group[1]
                ],
            )

    def build_user_menu(self, request: Request) -> UserMenu:
        return self.auth_policy.get_user_menu(request)

    def url_for(self, request: Request, path_name: str, **path_params: typing.Any) -> str:
        return request.url_for(path_name, **path_params)

    def static_url(self, request: Request, path: str) -> str:
        return self.url_for(request, 'ohmyadmin_static', path=path) + f'?{time.time()}'

    def get_routes(self) -> typing.Iterable[BaseRoute]:
        yield Route('/', self.index_view, name='ohmyadmin_welcome')
        yield Route('/login', self.login_view, name='ohmyadmin_login', methods=['GET', 'POST'])
        yield Route('/logout', self.logout_view, name='ohmyadmin_logout', methods=['POST'])
        yield Mount('/static', StaticFiles(packages=[__name__.split('.')[0]]), name='ohmyadmin_static')

        if self.file_storage:
            yield Mount('/media', MediaServer(self.file_storage), name='ohmyadmin_media')

        for resource in self.resources:
            yield Mount(f'/resources/{resource.slug}', resource)

        for page in self.pages:
            yield Mount(f'/{page.id}', page)

        for dashboard in self.dashboards:
            yield Mount(f'/dashboard/{dashboard.slug}', dashboard)

    async def index_view(self, request: Request) -> Response:
        return TemplateResponse(
            'ohmyadmin/index.html',
            {
                'page_title': _('Welcome'),
                **admin_context(request),
            },
        )

    async def login_view(self, request: Request) -> Response:
        next_url = request.query_params.get('next', request.url_for('ohmyadmin_welcome'))
        form_class = self.auth_policy.get_login_form_class()
        form = form_class(formdata=await request.form(), data={'next_url': next_url})
        if request.method in ['POST'] and form.validate():
            if user := await self.auth_policy.authenticate(request, form.identity.data, form.password.data):
                self.auth_policy.login(request, user)
                flash(request).success(_('You have been logged in.'))
                return RedirectResponse(url=form.next_url.data, status_code=302)
            else:
                flash(request).error(_('Invalid credentials.'))

        form_layout = Grid(children=[FormElement(field) for field in form])
        return TemplateResponse(
            'ohmyadmin/login.html',
            {
                'request': request,
                'form': form,
                'next_url': next_url,
                'form_layout': form_layout,
                'page_title': _('Login'),
                **admin_context(request),
            },
        )

    async def logout_view(self, request: Request) -> Response:
        self.auth_policy.logout(request)
        flash(request).success(_('You have been logged out.'))
        return RedirectResponse(request.url_for('ohmyadmin_login'), status_code=302)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        from ohmyadmin.globals import globalize_admin

        request = Request(scope, receive)
        with globalize_admin(self), globalize_request(request):
            scope.setdefault('state', {})
            scope['state']['admin'] = self
            scope['state']['file_storage'] = self.file_storage
            scope['state']['auth_policy'] = self.auth_policy
            app = super().__call__
            for middleware in reversed(self.middleware):
                app = middleware.cls(app, **middleware.options)

            await app(scope, receive, send)
