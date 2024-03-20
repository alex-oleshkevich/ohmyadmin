import time

from starlette.datastructures import URL
from starlette.requests import Request


def static_url(request: Request, path: str) -> URL:
    if path.startswith("http://") or path.startswith("https://"):
        return URL(path)

    url = request.url_for("ohmyadmin.static", path=path)
    if request.app.debug:
        url = url.include_query_params(_ts=time.time())
    return url


def media_url(request: Request, path: str) -> URL:
    if path.startswith("http"):
        return URL(path)

    return request.url_for("ohmyadmin.media", path=path)


def url_matches(request: Request, url: URL | str) -> bool:
    value = str(url)
    return request.url.path.startswith(value)
