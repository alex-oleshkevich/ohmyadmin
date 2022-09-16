from __future__ import annotations

import re
import typing
from starlette.requests import Request

from ohmyadmin.globals import get_current_admin, get_current_request
from ohmyadmin.responses import Response
from ohmyadmin.templating import jinja_env


def render_to_string(template_name: str, context: dict[str, typing.Any] | None = None) -> str:
    template = jinja_env.get_template(template_name)
    return template.render(context or {})


def render_to_response(
    request: Request, template_name: str, context: dict[str, typing.Any] | None = None, status_code: int = 200
) -> Response:
    return get_current_admin().render_to_response(request, template_name, context, status_code)


def camel_to_sentence(text: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', text)


def route(path_name: str, **path_params: str | int) -> str:
    return get_current_request().url_for(path_name, **(path_params or {}))


def media_url(path: str) -> str:
    return get_current_request().url_for('admin_media', path=path)
