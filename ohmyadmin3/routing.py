from __future__ import annotations

from dataclasses import dataclass

import typing
from starlette.requests import Request
from starlette.responses import Response


@dataclass
class RouteSpec:
    path: str
    name: str | None = None
    methods: list[str] | None = None


def route(path: str, methods: list[str] | None = None, path_name: str | None = None) -> typing.Callable:
    def wrapper(
        view: typing.Callable[[Request], typing.Awaitable[Response]]
    ) -> typing.Callable[[Request], typing.Awaitable[Response]]:
        setattr(view, '__route_spec__', RouteSpec(path=path, name=path_name, methods=methods))
        return view

    return wrapper
