import time

from starlette.datastructures import URL
from starlette.requests import Request


def static_url(request: Request, path: str) -> str:
    url = request.url_for('ohmyadmin.static', path=path)
    if request.app.debug:
        url = url.include_query_params(_ts=time.time())
    return str(url)


def url_matches(request: Request, url: URL | str) -> bool:
    value = str(url)
    return request.url.path.startswith(value)
