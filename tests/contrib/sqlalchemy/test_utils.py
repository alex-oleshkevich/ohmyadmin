from starlette.requests import Request
from unittest import mock

from ohmyadmin.contrib.sqlalchemy.utils import choices_from
from tests.contrib.sqlalchemy.models import Post


async def test_choices_from(http_request: Request) -> None:
    http_request.state.dbsession = mock.AsyncMock()
    http_request.state.dbsession.scalars = mock.AsyncMock(
        return_value=[Post(id=1, title='one'), Post(id=2, title='two')]
    )

    loader = choices_from(Post, value_column='id', label_column='title')
    assert await loader(http_request) == [(1, 'one'), (2, 'two')]
