from __future__ import annotations

import functools
import os
import typing

import jinja2
from async_storages import FileStorage, MemoryBackend
from async_storages.contrib.starlette import FileServer
from starlette import templating
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import BaseRoute, Mount, Route, Router
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send
from starlette_babel import gettext_lazy as _
from starlette_babel.contrib.jinja import configure_jinja_env
from starlette_babel.locale import get_language
from starlette_flash import flash

from ohmyadmin.authentication import AnonymousAuthPolicy, AuthPolicy, LoginRequiredMiddleware
from ohmyadmin.pages import Page
from ohmyadmin.templating import media_url, static_url, url_matches
from ohmyadmin.theme import Theme

PACKAGE_NAME = __name__.split(".")[0]


class OhMyAdmin(Router):
    def __init__(
        self,
        app_name: str = "OhMyAdmin!",
        pages: typing.Sequence[Page] = tuple(),
        theme: Theme = Theme(),
        file_storage: FileStorage | None = None,
        auth_policy: AuthPolicy | None = None,
        template_dirs: typing.Sequence[str | os.PathLike[str]] = tuple(),
        template_packages: typing.Sequence[str] = tuple(),
    ) -> None:
        self.pages = pages
        self.theme = theme
        self.app_name = app_name
        self.file_storage = file_storage or FileStorage(storage=MemoryBackend())
        self.auth_policy = auth_policy or AnonymousAuthPolicy()
        self.jinja_env = self.configure_jinja(template_dirs, template_packages)
        self.templating = templating.Jinja2Templates(env=self.jinja_env, context_processors=[self.template_context])

        super().__init__(
            routes=self.get_routes(),
            middleware=[
                Middleware(
                    AuthenticationMiddleware,
                    backend=self.auth_policy.get_authentication_backend(),
                ),
                Middleware(LoginRequiredMiddleware, exclude_paths=["/login", "/static", "/site.webmanifest"]),
            ],
        )

    def configure_jinja(
        self,
        template_dirs: typing.Sequence[str | os.PathLike[str]] = tuple(),
        template_packages: typing.Sequence[str] = tuple(),
    ) -> jinja2.Environment:
        loaders: list[jinja2.BaseLoader] = [jinja2.PackageLoader(PACKAGE_NAME)]
        loaders.append(jinja2.FileSystemLoader(list(template_dirs)))
        loaders.extend([jinja2.PackageLoader(template_package) for template_package in template_packages])

        env = jinja2.Environment(
            autoescape=True,
            undefined=jinja2.StrictUndefined,
            loader=jinja2.ChoiceLoader(loaders),
        )
        configure_jinja_env(env)
        return env

    def template_context(self, request: Request) -> dict[str, typing.Any]:
        return {
            "app": self,
            "theme": self.theme,
            "request": request,
            "app_language": get_language(),
            "static_url": functools.partial(static_url, request),
            "media_url": functools.partial(media_url, request),
            "url_matches": functools.partial(url_matches, request),
            "flash_messages": flash(request),
        }

    def get_routes(self) -> list[BaseRoute]:
        return [
            Route("/", self.welcome_view, name="ohmyadmin.welcome"),
            Route("/login", self.login_view, name="ohmyadmin.login", methods=["get", "post"]),
            Route("/logout", self.logout_view, name="ohmyadmin.logout", methods=["post"]),
            Route("/site.webmanifest", self.webmanifest_view, name="ohmyadmin.webmanifest"),
            Mount("/static", app=StaticFiles(packages=[PACKAGE_NAME]), name="ohmyadmin.static"),
            Mount("/media", app=FileServer(self.file_storage), name="ohmyadmin.media"),
        ]

    async def welcome_view(self, request: Request) -> Response:
        return self.templating.TemplateResponse(
            request,
            "ohmyadmin/welcome.html",
            {"page_title": _("Welcome", domain="ohmyadmin")},
        )

    async def login_view(self, request: Request) -> Response:
        next_url = request.query_params.get("next", request.url_for("ohmyadmin.welcome"))
        form_class = self.auth_policy.get_login_form_class()
        form = form_class(formdata=await request.form(), data={"next_url": next_url})
        if request.method in ["POST"] and form.validate():
            identity = typing.cast(str, form.identity.data)
            password = typing.cast(str, form.password.data)
            if user := await self.auth_policy.authenticate(request, identity, password):
                self.auth_policy.login(request, user)
                flash(request).success(_("You have been logged in.", domain="ohmyadmin"))
                return RedirectResponse(url=typing.cast(str, form.next_url.data), status_code=302)
            else:
                flash(request).error(_("Invalid credentials.", domain="ohmyadmin"))

        return self.templating.TemplateResponse(
            request,
            "ohmyadmin/login.html",
            {"page_title": _("Login", domain="ohmyadmin"), "form": form},
        )

    async def logout_view(self, request: Request) -> Response:
        self.auth_policy.logout(request)
        flash(request).success(_("You have been logged out.", domain="ohmyadmin"))
        redirect_url = request.url_for("ohmyadmin.login")
        return RedirectResponse(redirect_url, status_code=302)

    async def webmanifest_view(self, request: Request) -> Response:
        return JSONResponse(
            {
                "name": self.app_name,
                "short_name": self.app_name,
                "background_color": self.theme.background_color,
                "theme_color": self.theme.navbar_color,
                "start_url": str(request.url_for("ohmyadmin.welcome").include_query_params(utm_source="welcome")),
                "icons": [{"src": self.theme.icon_url, "type": "image/png", "sizes": "512x512"}],
            }
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope.setdefault("state")
        scope["state"]["ohmyadmin"] = self
        await super().__call__(scope, receive, send)
