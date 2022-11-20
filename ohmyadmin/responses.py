from __future__ import annotations

import json
import typing
from starlette import responses
from starlette.datastructures import URL
from starlette_flash import FlashCategory


class HXResponse(responses.Response):
    def __init__(self, events: dict[str, typing.Any] | None = None) -> None:
        self.events = events or {}
        super().__init__()

    def trigger_event(self, name: str, value: typing.Any = '') -> HXResponse:
        self.events[name] = value
        self.headers['hx-trigger'] = json.dumps(self.events)
        return self

    def show_toast(self, message: str, category: FlashCategory = 'success') -> HXResponse:
        """
        Show toast (flash message).

        Only works in HTMX context.
        """
        return self.trigger_event('toast', {'message': message, 'category': category})

    def redirect(self, url: str | URL) -> HXResponse:
        """
        Perform client page redirect.

        Only works in HTMX context.
        """
        self.headers['hx-redirect'] = str(url)
        return self

    def refresh(self) -> HXResponse:
        """
        Perform client page refresh.

        Only works in HTMX context.
        """
        self.headers['hx-refresh'] = 'true'
        return self
