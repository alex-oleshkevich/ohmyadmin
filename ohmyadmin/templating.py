import time
import typing

from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import HTMLResponse


def static_url(request: Request, path: str) -> str:
    url = request.url_for('ohmyadmin.static', path=path)
    if request.app.debug:
        url = url.include_query_params(_ts=time.time())
    return str(url)


def url_matches(request: Request, url: URL | str) -> bool:
    value = str(url)
    return request.url.path.startswith(value)


def render_to_response(
    request: Request, name: str,
    context: typing.Mapping[str, typing.Any] | None = None,
    status_code: int = 200, headers: typing.Mapping[str, str] | None = None,
) -> HTMLResponse:
    return request.state.ohmyadmin.templating.TemplateResponse(
        request, name,
        context=context,
        status_code=status_code,
        headers=headers,
    )
