import contextlib
import contextvars
import typing
from starlette.requests import Request
from starlette.responses import Response

from ohmyadmin.app import OhMyAdmin
from ohmyadmin.templating import jinja_env

_app: contextvars.ContextVar[OhMyAdmin] = contextvars.ContextVar('_app')
_template_context: contextvars.ContextVar[dict[str, typing.Any]] = contextvars.ContextVar(
    '_template_context',
    default={},
)


@contextlib.contextmanager
def globalize_admin(admin: OhMyAdmin) -> typing.Iterable[None]:
    _app.set(admin)
    yield
    _app.reset()


def get_current_admin() -> OhMyAdmin:
    return _app.get()


@contextlib.contextmanager
def globalize_template_context(context: dict[str, typing.Any]) -> typing.Iterable[None]:
    _template_context.set(context)
    yield
    _template_context.reset()


def get_current_template_context() -> dict[str, typing.Any]:
    return _template_context.get()


def render_to_string(template_name: str, context: dict[str, typing.Any] | None = None) -> str:
    template = jinja_env.get_template(template_name)
    return template.render(context or {})


def render_to_response(
    request: Request, template_name: str, context: dict[str, typing.Any] | None = None, status_code: int = 200
) -> Response:
    return get_current_admin().render_to_response(request, template_name, context, status_code)
