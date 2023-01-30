import pytest
from starlette.testclient import TestClient

from tests.conftest import CreateTestAppFactory
from tests.resources.demo_resource import DemoResource


@pytest.fixture
def client(create_test_app: CreateTestAppFactory) -> TestClient:
    app = create_test_app(pages=[DemoResource()])
    return TestClient(app)
