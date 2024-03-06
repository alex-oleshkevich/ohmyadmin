from __future__ import annotations

import typing

from starlette.datastructures import URL
from starlette.requests import Request


class URLProvider(typing.Protocol):
    url_name: str


class LazyURL:
    def __init__(self, route_name: str, **params: typing.Any) -> None:
        self.route_name = route_name
        self.params = params or {}

    def resolve(self, request: Request) -> URL:
        return request.url_for(self.route_name, **self.params)


def url_to(screen: URLProvider, **params: typing.Any) -> LazyURL:
    return LazyURL(screen.url_name, **params)
