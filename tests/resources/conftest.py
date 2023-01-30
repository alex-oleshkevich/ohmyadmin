import pytest
from starlette.testclient import TestClient

from ohmyadmin.datasource.memory import InMemoryDataSource
from tests.conftest import CreateTestAppFactory
from tests.models import Post
from tests.resources.demo_resource import DemoResource


@pytest.fixture
def demo_datasource() -> InMemoryDataSource[Post]:
    return InMemoryDataSource(Post, [Post(id=x, title=f'Title {x}') for x in range(1, 100)])


@pytest.fixture
def client(create_test_app: CreateTestAppFactory, demo_datasource: InMemoryDataSource[Post]) -> TestClient:
    resource = DemoResource()
    resource.datasource = demo_datasource
    app = create_test_app(pages=[resource])
    return TestClient(app)
