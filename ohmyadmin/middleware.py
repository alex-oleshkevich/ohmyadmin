from starlette.requests import HTTPConnection, Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette_babel import gettext_lazy as _
from starlette_flash import flash


class LoginRequiredMiddleware:
    def __init__(self, app: ASGIApp, exclude_paths: list[str]) -> None:
        self.app = app
        self.exclude_paths = exclude_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        conn = HTTPConnection(scope)
        if conn.user.is_authenticated or any(
            [excluded_path in conn.url.path for excluded_path in self.exclude_paths]
        ):
            await self.app(scope, receive, send)
            return

        if scope["type"] == "http":
            flash(Request(scope)).error(
                _("You need to be logged in to access this page.", domain="ohmyadmin")
            )

        redirect_to = conn.url_for("ohmyadmin.login").include_query_params(
            next=conn.url.path
        )
        response = RedirectResponse(url=redirect_to, status_code=302)
        await response(scope, receive, send)
