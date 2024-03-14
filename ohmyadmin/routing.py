from __future__ import annotations

import typing

from starlette.datastructures import URL
from starlette.requests import Request


class URLProvider(typing.Protocol):
    url_name: str


class LazyURL:
    def __init__(
        self,
        route_name: str,
        query_params: typing.Mapping[str, typing.Any] | None = None,
        path_params: typing.Mapping[str, typing.Any] | None = None,
    ) -> None:
        self.route_name = route_name
        self.query_params = query_params or {}
        self.path_params = path_params or {}

    def resolve(self, request: Request) -> URL:
        url = request.url_for(self.route_name, **self.path_params)
        for query_param, value in self.query_params.items():
            if isinstance(value, (list, tuple, set)):
                for subvalue in value:
                    url = url.include_query_params(**{query_param: subvalue})
            else:
                url = url.include_query_params(**{query_param: value})

        return url


def url_to(screen: URLProvider, **params: typing.Any) -> LazyURL:
    return LazyURL(screen.url_name, path_params=params)


URLType = str | URL | LazyURL


def resolve_url(request: Request, url: URLType) -> URL:
    if isinstance(url, (URL, str)):
        return URL(str(url))

    return url.resolve(request)
