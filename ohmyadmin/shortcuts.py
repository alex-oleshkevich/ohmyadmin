from __future__ import annotations

import typing
from starlette.requests import HTTPConnection, Request
from starlette.responses import Response

if typing.TYPE_CHECKING:  # pragma:no cover
    from ohmyadmin.app import OhMyAdmin


def get_admin(conn: HTTPConnection) -> OhMyAdmin:
    return conn.state.admin


def render_to_string(
    request: Request,
    template_name: str,
    context: typing.Mapping[str, typing.Any] | None = None,
) -> str:
    return request.state.admin.render_to_string(request, template_name, context)


def render_to_response(
    request: Request,
    template_name: str,
    context: typing.Mapping[str, typing.Any] | None = None,
    headers: typing.Mapping[str, typing.Any] | None = None,
) -> Response:
    return request.state.admin.render_to_response(request, template_name, context, headers=headers)
