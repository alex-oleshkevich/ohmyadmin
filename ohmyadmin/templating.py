import functools
import time
import typing

import jinja2
import markupsafe
from markupsafe import Markup
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import HTMLResponse


def static_url(request: Request, path: str) -> str:
    url = request.url_for("ohmyadmin.static", path=path)
    if request.app.debug:
        url = url.include_query_params(_ts=time.time())
    return str(url)


def media_url(request: Request, path: str) -> URL:
    if path.startswith("http"):
        return URL(path)

    return request.url_for("ohmyadmin.media", path=path)


def url_matches(request: Request, url: URL | str) -> bool:
    value = str(url)
    return request.url.path.startswith(value)


@jinja2.pass_context
def model_pk(context: jinja2.runtime.Context, obj: typing.Any, request: Request | None = None) -> str:
    """Try to infer the model's primary key value."""
    request = request or context["request"]

    # try to get from current resource
    try:
        resource = request.state.resource
        return resource.datasource.get_pk(obj)
    except AttributeError:
        try:
            screen = request.state.screen
            return screen.datasource.get_pk(obj)
        except AttributeError:
            # still no luck? let's iterate over all registered resources and  may be some of them can parse it
            for screen in request.state.ohmyadmin.screens:
                if hasattr(screen, "datasource"):
                    return screen.datasource.get_pk(obj)

            raise ValueError(f"Can't infer primary key. No datasource found for {type(obj).__name__}")


def to_html_attrs(attrs: typing.Mapping[str, typing.Any]) -> str:
    def clean_key(key: str) -> str:
        key = key.rstrip("_")
        if key.startswith("data_") or key.startswith("aria_"):
            key = key.replace("_", "-")
        return key

    parts = []
    for key, value in sorted(attrs.items()):
        key = clean_key(key)
        if value is True:
            parts.append(key)
        elif value is False or value is None:
            pass
        else:
            parts.append(f'{key}="{markupsafe.escape(value)}"')

    return ' '.join(parts).strip()


def render_to_response(
    request: Request,
    name: str,
    context: typing.Mapping[str, typing.Any] | None = None,
    status_code: int = 200,
    headers: typing.Mapping[str, str] | None = None,
) -> HTMLResponse:
    return request.state.ohmyadmin.templating.TemplateResponse(
        request,
        name,
        context=context,
        status_code=status_code,
        headers=headers,
    )


def render_to_string(request: Request, name: str, context: typing.Mapping[str, typing.Any] | None = None) -> str:
    context = dict(context or {})
    context.update(
        {
            "request": request,
            "media_url": functools.partial(media_url, request),
            "static_url": functools.partial(static_url, request),
        }
    )
    content = request.state.ohmyadmin.templating.env.get_template(name).render(context)
    return Markup(content)
