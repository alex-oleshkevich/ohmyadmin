from __future__ import annotations

import contextlib
import contextvars
import typing
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

if typing.TYPE_CHECKING:
    from ohmyadmin.app import OhMyAdmin

_session: contextvars.ContextVar[AsyncSession] = contextvars.ContextVar('_session')
_app: contextvars.ContextVar[OhMyAdmin] = contextvars.ContextVar('_app')
_request: contextvars.ContextVar[Request] = contextvars.ContextVar('_request')
_template_context: contextvars.ContextVar[dict[str, typing.Any]] = contextvars.ContextVar(
    '_template_context',
    default={},
)


@contextlib.contextmanager
def globalize_dbsession(session: AsyncSession) -> typing.Iterator[None]:
    token = _session.set(session)
    yield
    _session.reset(token)


def get_dbsession() -> AsyncSession:
    return _session.get()


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


@contextlib.contextmanager
def globalize_request(request: Request) -> typing.Iterator[None]:
    reset_token = _request.set(request)
    yield
    _request.reset(reset_token)


def get_current_request() -> Request:
    return _request.get()
