import functools
import time
import typing

import jinja2
from markupsafe import Markup
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import HTMLResponse


def static_url(request: Request, path: str) -> str:
    url = request.url_for("ohmyadmin.static", path=path)
    if request.app.debug:
        url = url.include_query_params(_ts=time.time())
    return str(url)


def media_url(request: Request, path: str) -> str:
    if path.startswith("http"):
        return path

    raise NotImplementedError()


def url_matches(request: Request, url: URL | str) -> bool:
    value = str(url)
    return request.url.path.startswith(value)


@jinja2.pass_context
def model_pk(context: jinja2.runtime.Context, obj: typing.Any) -> str:
    """Try to infer the model's primary key value."""
    request: Request = context["request"]

    # try to get from current resource
    try:
        resource = request.state.resource
        return resource.datasource.get_pk(obj)
    except AttributeError:
        try:
            view = request.state.view
            return view.datasource.get_pk(obj)
        except AttributeError:
            # still no luck? let's iterate over all registered resources and  may be some of them can parse it
            for view in request.state.ohmyadmin.views:
                if hasattr(view, "datasource"):
                    return view.datasource.get_pk(obj)

            raise ValueError(f"Can't infer primary key. No datasource found for {type(obj).__name__}")


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
