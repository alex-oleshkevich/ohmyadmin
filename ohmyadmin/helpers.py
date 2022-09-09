from __future__ import annotations

import contextlib
import contextvars
import typing
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.templating import jinja_env

if typing.TYPE_CHECKING:
    from ohmyadmin.app import OhMyAdmin

_app: contextvars.ContextVar[OhMyAdmin] = contextvars.ContextVar('_app')
_template_context: contextvars.ContextVar[dict[str, typing.Any]] = contextvars.ContextVar(
    '_template_context',
    default={},
)


@contextlib.contextmanager
def globalize_admin(admin: OhMyAdmin) -> typing.Iterator[None]:
    reset_token = _app.set(admin)
    yield
    _app.reset(reset_token)


def get_current_admin() -> OhMyAdmin:
    return _app.get()


@contextlib.contextmanager
def globalize_template_context(context: dict[str, typing.Any]) -> typing.Iterator[None]:
    token = _template_context.set(context)
    yield
    _template_context.reset(token)


def get_current_template_context() -> dict[str, typing.Any]:
    return _template_context.get()


def render_to_string(template_name: str, context: dict[str, typing.Any] | None = None) -> str:
    template = jinja_env.get_template(template_name)
    return template.render(context or {})


def render_to_response(
    request: Request, template_name: str, context: dict[str, typing.Any] | None = None, status_code: int = 200
) -> Response:
    return get_current_admin().render_to_response(request, template_name, context, status_code)
