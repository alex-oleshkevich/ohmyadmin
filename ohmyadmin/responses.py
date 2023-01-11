from __future__ import annotations

import json
import typing
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.helpers import LazyURL


class ActionResponse(Response):
    def __init__(
        self,
        status_code: int = 204,
        headers: dict[str, typing.Any] | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        super().__init__(status_code=status_code, headers=headers, background=background)

    def show_toast(self, message: str, category: typing.Literal['success', 'error'] = 'success') -> ActionResponse:
        return self.trigger('toast', {'message': message, 'category': category})

    def redirect(self, request: Request, url: str | LazyURL) -> ActionResponse:
        """Triggers a client-side redirect to a new location."""
        self.headers['hx-redirect'] = url.resolve(request) if isinstance(url, LazyURL) else url
        return self

    def refresh(self, request: Request, url: str | LazyURL) -> ActionResponse:
        """Trigger full refresh of the page."""
        self.headers['hx-refresh'] = url.resolve(request) if isinstance(url, LazyURL) else url
        return self

    def refresh_datatable(self) -> ActionResponse:
        return self.trigger('refresh-datatable')

    def trigger(self, event: str, data: str | dict[str, str | float] = '') -> ActionResponse:
        payload = json.loads(self.headers.get('hx-trigger', '{}'))
        payload[event] = data
        self.headers['hx-trigger'] = json.dumps(payload)
        return self
