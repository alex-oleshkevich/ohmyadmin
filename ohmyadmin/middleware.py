from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class LoginRequiredMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope)
        if request.user.is_authenticated:
            await self.app(scope, receive, send)
        else:
            response = RedirectResponse(url=request.url_for('ohmyadmin.login'))
            await response(scope, receive, send)
