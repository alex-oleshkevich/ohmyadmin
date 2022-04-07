from __future__ import annotations

from dataclasses import dataclass

import typing
from starlette import routing
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send
from unittest import mock

from ohmyadmin.request import AdminRequest


@dataclass
class RouteSpec:
    path: str
    name: str | None = None
    methods: list[str] | None = None


def route(path: str, methods: list[str] | None = None, path_name: str | None = None) -> typing.Callable:
    def wrapper(
        view: typing.Callable[[AdminRequest], typing.Awaitable[Response]]
    ) -> typing.Callable[[AdminRequest], typing.Awaitable[Response]]:
        setattr(view, '__route_spec__', RouteSpec(path=path, name=path_name, methods=methods))
        return view

    return wrapper


def request_response(func: typing.Callable) -> ASGIApp:
    """Takes a function or coroutine `func(request) -> response`, and returns an
    ASGI application."""
    is_coroutine = routing.iscoroutinefunction_or_partial(func)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = AdminRequest(scope, receive=receive, send=send)
        if is_coroutine:
            response = await func(request, **request.path_params)
        else:
            response = await run_in_threadpool(func, request, **request.path_params)
        await response(scope, receive, send)

    return app


class Route(routing.Route):
    def __init__(
        self, path: str, endpoint: typing.Callable, *, methods: list[str] | None = None, name: str | None = None
    ) -> None:
        with mock.patch.object(routing, 'request_response', request_response):
            super().__init__(path, endpoint, methods=methods, name=name)
