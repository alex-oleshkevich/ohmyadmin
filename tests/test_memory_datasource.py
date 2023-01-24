import dataclasses

import pytest
from starlette.requests import Request

from ohmyadmin.datasource.memory import InMemoryDataSource


@dataclasses.dataclass
class Post:
    id: int = 1
    title: str = 'Title'
    published: bool = False


@pytest.fixture
def datasource() -> InMemoryDataSource[Post]:
    return InMemoryDataSource(Post, [
        Post(id=index, title=f'Title {index}', published=index % 5 == 0) for index in range(20)
    ])


@pytest.fixture()
def http_request() -> Request:
    return Request(scope={'type': 'http'})


def test_get_pk(datasource: InMemoryDataSource) -> None:
    obj = Post(id=1)
    assert datasource.get_pk(obj) == '1'


async def test_get(datasource: InMemoryDataSource[Post], http_request: Request) -> None:
    obj = await datasource.get(http_request, '2')
    assert obj.id == 2
