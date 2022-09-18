import functools
import jinja2
import os
import pathlib
import time
import typing
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send

from ohmyadmin.auth import AnonymousAuthPolicy, BaseAuthPolicy, RequireLoginMiddleware, UserMenu
from ohmyadmin.components import Component, FormElement, Grid, MenuGroup, MenuItem
from ohmyadmin.dashboards import Dashboard
from ohmyadmin.flash import FlashMiddleware, flash
from ohmyadmin.globals import globalize_dbsession, globalize_request
from ohmyadmin.i18n import _
from ohmyadmin.media_server import MediaServer
from ohmyadmin.pages import Page
from ohmyadmin.resources import Resource
from ohmyadmin.responses import RedirectResponse, Response
from ohmyadmin.storage import FileStorage
from ohmyadmin.structures import URLSpec
from ohmyadmin.templating import DynamicChoiceLoader, jinja_env

this_dir = pathlib.Path(__file__).parent


class OhMyAdmin(Router):
    def __init__(
        self,
        engine: AsyncEngine,
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
        self.engine = engine
        self.title = title
        self.logo_url = logo_url
        self._make_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        self.file_storage = file_storage
        self.pages = pages or []
        self.resources = resources or []
        self.dashboards = dashboards or []
        self.auth_policy = auth_policy or AnonymousAuthPolicy()
        self.middleware = list(middleware or [])
        self.middleware.extend(
            [
                Middleware(FlashMiddleware),
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

    def build_main_menu(self, request: Request) -> typing.Iterable[Component]:
        for dashboard in self.dashboards:
            yield MenuItem(text=dashboard.label, icon=dashboard.icon, url=URLSpec.to_dashboard(dashboard))

        yield MenuGroup(
            text=_('Resources'),
            items=[
                MenuItem(text=resource.label, icon=resource.icon, url=URLSpec.to_resource(resource.__class__))
                for resource in self.resources
            ],
        )
        yield MenuGroup(
            text=_('Pages'),
            items=[MenuItem(text=page.label, icon=page.icon, url=URLSpec.to_page(page)) for page in self.pages],
        )

    def build_user_menu(self, request: Request) -> UserMenu:
        return self.auth_policy.get_user_menu(request)

    def url_for(self, request: Request, path_name: str, **path_params: typing.Any) -> str:
        return request.url_for(path_name, **path_params)

    def static_url(self, request: Request, path: str) -> str:
        return self.url_for(request, 'ohmyadmin_static', path=path) + f'?{time.time()}'

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
        yield Route('/', self.index_view, name='ohmyadmin_welcome')
        yield Route('/login', self.login_view, name='ohmyadmin_login', methods=['GET', 'POST'])
        yield Route('/logout', self.logout_view, name='ohmyadmin_logout', methods=['POST'])
        yield Mount('/static', StaticFiles(packages=[__name__.split('.')[0]]), name='ohmyadmin_static')

        if self.file_storage:
            yield Mount('/media', MediaServer(self.file_storage), name='ohmyadmin_media')

        for resource in self.resources:
            yield Mount(f'/resources/{resource.id}', resource)

        for page in self.pages:
            yield Mount(f'/{page.id}', page)

        for dashboard in self.dashboards:
            yield Mount(f'/dashboard/{dashboard.id}', dashboard)

    async def index_view(self, request: Request) -> Response:
        return self.render_to_response(request, 'ohmyadmin/index.html')

    async def login_view(self, request: Request) -> Response:
        next_url = request.query_params.get('next', request.url_for('ohmyadmin_welcome'))
        form_class = self.auth_policy.get_login_form_class()
        form = await form_class.from_request(request, data={'next_url': next_url})
        if await form.validate_on_submit(request):
            if user := await self.auth_policy.authenticate(request, form.identity.data, form.password.data):
                self.auth_policy.login(request, user)
                return RedirectResponse(request, url=form.next_url.data).with_success(_('You have been logged in.'))
            else:
                flash(request).error(_('Invalid credentials.'))

        layout = Grid(children=[FormElement(field) for field in form])
        return self.render_to_response(
            request,
            'ohmyadmin/auth/login.html',
            {
                'request': request,
                'form': layout,
                'next_url': next_url,
                'page_title': _('Login'),
            },
        )

    async def logout_view(self, request: Request) -> Response:
        self.auth_policy.logout(request)
        return RedirectResponse(request).to_path_name('ohmyadmin_login').with_success(_('You have been logged out.'))

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        from ohmyadmin.globals import globalize_admin

        request = Request(scope, receive)
        async with self._make_session() as session:
            with globalize_admin(self), globalize_request(request), globalize_dbsession(session):
                scope.setdefault('state', {})
                scope['state']['admin'] = self
                scope['state']['file_storage'] = self.file_storage
                scope['state']['auth_policy'] = self.auth_policy
                scope['state']['dbsession'] = session
                app = super().__call__
                for middleware in reversed(self.middleware):
                    app = middleware.cls(app, **middleware.options)

                await app(scope, receive, send)
