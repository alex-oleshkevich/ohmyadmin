import pathlib
import pytest
import typing
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from ohmyadmin.pages.page import Page
from tests.conftest import CreateTestAppFactory


@pytest.mark.parametrize('method', ['get', 'post', 'put', 'patch', 'delete'])
def test_generates_routes(create_test_app: CreateTestAppFactory, method: str) -> None:
    """
    Page class should generate routes for HTTP verbs.

    For example, when DummyPage defines `get` and `post` then the Route instance must support them too.
    """

    class DummyPage(Page):
        slug = 'dummy'

        async def get(self, request: Request) -> Response:
            return Response('ok')

        async def post(self, request: Request) -> Response:
            return Response('ok')

        async def put(self, request: Request) -> Response:
            return Response('ok')

        async def patch(self, request: Request) -> Response:
            return Response('ok')

        async def delete(self, request: Request) -> Response:
            return Response('ok')

    client = TestClient(create_test_app(pages=[DummyPage()]))
    callback = getattr(client, method)
    response = callback('/admin/dummy', allow_redirects=False)
    assert response.status_code == 200


def test_not_generates_routes(create_test_app: CreateTestAppFactory) -> None:
    """Page class should NOT generate routes for HTTP verbs that a not defined on class."""

    class DummyPage(Page):
        slug = 'dummy'

    client = TestClient(create_test_app(pages=[DummyPage()]))
    response = client.post('/admin/dummy')
    assert response.status_code == 405


def test_default_handler(create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path) -> None:
    """Page should provide a default handler when none provided."""
    (extra_template_dir / 'sample.html').write_text('hello')

    class DummyPage(Page):
        slug = 'dummy'
        template = 'sample.html'

    client = TestClient(create_test_app(pages=[DummyPage()]))
    response = client.get('/admin/dummy')
    assert response.status_code == 200
    assert response.text == 'hello'


def test_default_handler_with_context(create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path) -> None:
    """When `handle` implemented, then it's context must be available in the template."""
    (extra_template_dir / 'sample.html').write_text('hello {{name}}')

    class DummyPage(Page):
        slug = 'dummy'
        template = 'sample.html'

        async def handle(self, request: Request) -> typing.Mapping[str, typing.Any]:
            return {'name': 'world'}

    client = TestClient(create_test_app(pages=[DummyPage()]))
    response = client.get('/admin/dummy')
    assert response.status_code == 200
    assert response.text == 'hello world'
