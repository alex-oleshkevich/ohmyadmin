import functools
import time
import typing

from markupsafe import Markup
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import HTMLResponse


def static_url(request: Request, path: str) -> str:
    url = request.url_for('ohmyadmin.static', path=path)
    if request.app.debug:
        url = url.include_query_params(_ts=time.time())
    return str(url)


def media_url(request: Request, path: str) -> str:
    if path.startswith('http'):
        return path

    raise NotImplementedError()


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


def render_to_string(request: Request, name: str, context: typing.Mapping[str, typing.Any] | None = None) -> str:
    context = context or {}
    context.update({
        'request': request,
        'media_url': functools.partial(media_url, request),
        'static_url': functools.partial(static_url, request),
    })
    content = request.state.ohmyadmin.templating.env.get_template(name).render(context)
    return Markup(content)
