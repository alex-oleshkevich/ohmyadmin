import functools
import itertools
import jinja2
import operator
import typing
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

from ohmyadmin.authentication.policy import AnonymousAuthPolicy, AuthPolicy
from ohmyadmin.menu import MenuItem
from ohmyadmin.middleware import LoginRequiredMiddleware
from ohmyadmin.storages.storage import FileStorage
from ohmyadmin.templating import static_url, url_matches
from ohmyadmin.theme import Theme
from ohmyadmin.views.base import View


class OhMyAdmin(Router):
    def __init__(
        self,
        views: list[View] | None = None,
        theme: Theme = Theme(),
        file_storage: FileStorage | None = None,
        auth_policy: AuthPolicy | None = None,
    ) -> None:
        self.theme = theme
        self.views = views or []
        self.auth_policy = auth_policy or AnonymousAuthPolicy()
        self.file_storage = file_storage

        self.jinja_env = jinja2.Environment(
            autoescape=True,
            undefined=jinja2.StrictUndefined,
            extensions=["jinja2.ext.do"],
            loader=jinja2.ChoiceLoader([jinja2.PackageLoader("ohmyadmin")]),
        )
        self.jinja_env.filters.update({"object_id": id})
        self.templating = templating.Jinja2Templates(
            env=self.jinja_env,
            context_processors=[
                self.context_processor,
            ],
        )
        configure_jinja_env(self.templating.env)
        super().__init__(routes=self.get_routes())

    def get_routes(self) -> list[BaseRoute]:
        return [
            Mount(
                path="",
                routes=[
                    Route("/", self.welcome_view, name="ohmyadmin.welcome"),
                    Route(
                        "/login",
                        self.login_view,
                        name="ohmyadmin.login",
                        methods=["get", "post"],
                    ),
                    Route(
                        "/logout",
                        self.logout_view,
                        name="ohmyadmin.logout",
                        methods=["post"],
                    ),
                    Mount(
                        "/static",
                        app=StaticFiles(packages=["ohmyadmin"]),
                        name="ohmyadmin.static",
                    ),
                    *[view.get_route() for view in self.views],
                ],
                middleware=[
                    Middleware(
                        AuthenticationMiddleware,
                        backend=self.auth_policy.get_authentication_backend(),
                    ),
                    Middleware(LoginRequiredMiddleware, exclude_paths=["/login", "/static"]),
                ],
            ),
        ]

    async def welcome_view(self, request: Request) -> Response:
        return self.templating.TemplateResponse(request, "ohmyadmin/welcome.html")

    async def login_view(self, request: Request) -> Response:
        next_url = request.query_params.get("next", request.url_for("ohmyadmin.welcome"))
        form_class = self.auth_policy.get_login_form_class()
        form = form_class(formdata=await request.form(), data={"next_url": next_url})
        if request.method in ["POST"] and form.validate():
            if user := await self.auth_policy.authenticate(request, form.identity.data, form.password.data):
                self.auth_policy.login(request, user)
                flash(request).success(_("You have been logged in.", domain="ohmyadmin"))
                return RedirectResponse(url=form.next_url.data, status_code=302)
            else:
                flash(request).error(_("Invalid credentials.", domain="ohmyadmin"))

        return self.templating.TemplateResponse(
            request,
            "ohmyadmin/login.html",
            {
                "page_title": _("Login"),
                "form": form,
            },
        )

    async def logout_view(self, request: Request) -> Response:
        self.auth_policy.logout(request)
        flash(request).success(_("You have been logged out."))
        return RedirectResponse(request.url_for("ohmyadmin.login"), status_code=302)

    async def generate_menu(self, request: Request) -> list[MenuItem]:
        groups = itertools.groupby(self.views, key=operator.attrgetter("group"))
        return [
            MenuItem(
                label=group[0],
                children=[await view.get_menu_item(request) for view in group[1]],
            )
            for group in groups
        ]

    def generate_user_menu(self, request: Request) -> list[MenuItem]:
        return []

    def context_processor(self, request: Request) -> dict[str, typing.Any]:
        return {
            "ohmyadmin": self,
            "theme": self.theme,
            "request": request,
            "static_url": functools.partial(static_url, request),
            "url_matches": functools.partial(url_matches, request),
            "flash_messages": flash(request),
            "ohmyadmin_main_menu": request.scope["ohmyadmin_main_menu"],
            "ohmyadmin_user_menu": request.scope["ohmyadmin_user_menu"],
        }

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope.setdefault("state")
        scope["state"]["ohmyadmin"] = self
        scope["ohmyadmin_main_menu"] = await self.generate_menu(Request(scope))
        scope["ohmyadmin_user_menu"] = self.generate_user_menu(Request(scope))
        await super().__call__(scope, receive, send)
