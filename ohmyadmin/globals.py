import contextlib
import contextvars
import typing
from sqlalchemy.ext.asyncio import AsyncSession

_session: contextvars.ContextVar[AsyncSession] = contextvars.ContextVar('_session')


@contextlib.contextmanager
def with_dbsession(session: AsyncSession) -> typing.Iterator[None]:
    token = _session.set(session)
    yield
    _session.reset(token)


def get_dbsession() -> AsyncSession:
    return _session.get()
