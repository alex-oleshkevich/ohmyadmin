from __future__ import annotations

import typing
from starlette import responses
from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.types import Receive, Scope, Send

from ohmyadmin.flash import FlashBag, FlashCategory

if typing.TYPE_CHECKING:
    from ohmyadmin.resources import Resource, ResourceAction


class Response:
    def __init__(
        self,
        content: str | None = None,
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
        media_type: str | None = None,
    ) -> None:
        self.headers = MutableHeaders(headers)
        self.content = content
        self.status_code = status_code
        self.media_type = media_type

    def add_header(self, name: str, value: str) -> Response:
        self.headers.append(name, value)
        return self

    def add_headers(self, headers: typing.Mapping[str, str]) -> Response:
        for name, value in headers.items():
            self.add_header(name, value)
        return self

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = responses.Response(self.content, self.status_code, self.headers, media_type=self.media_type)
        await response(scope, receive, send)


class RedirectResponse(Response):
    def __init__(
        self,
        request: Request,
        url: str | None = None,
        status_code: int = 302,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url
        self.message = ''
        self.message_category: FlashCategory = 'success'
        self.request = request
        super().__init__(status_code=status_code, headers=headers)

    def to_resource(
        self,
        resource: Resource | typing.Type[Resource],
        action: ResourceAction = 'list',
        pk: int | str | None = None,
    ) -> RedirectResponse:
        kwargs = {'pk': pk} if pk else {}
        self.url = self.request.url_for(resource.get_route_name(action), **kwargs)
        return self

    def to_path_name(
        self,
        path_name: str,
        path_params: typing.Mapping[str, str | int] | None = None,
    ) -> RedirectResponse:
        path_params = path_params or {}
        self.url = self.request.url_for(path_name, **path_params)
        return self

    def with_message(self, message: str, category: FlashCategory = 'success') -> RedirectResponse:
        self.message = message
        self.message_category = category
        return self

    def with_success(self, message: str) -> RedirectResponse:
        return self.with_message(message, 'success')

    def with_error(self, message: str) -> RedirectResponse:
        return self.with_message(message, 'error')

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.message:
            flashes: FlashBag = scope['state']['flash_messages']
            flashes.add(self.message, self.message_category)

        assert self.url
        response = responses.RedirectResponse(self.url, self.status_code, self.headers)
        await response(scope, receive, send)
