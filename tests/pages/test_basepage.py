import pathlib
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from ohmyadmin.pages.base import BasePage
from tests.conftest import CreateTestAppFactory


def test_automatically_generates_slug(create_test_app: CreateTestAppFactory) -> None:
    """BasePage should automatically generate slug attribute based on label."""

    class DummyPage(BasePage):
        pass

    page = DummyPage()
    assert page.slug == 'dummy'


def test_automatically_generates_label(create_test_app: CreateTestAppFactory) -> None:
    """BasePage should automatically generate label attribute based on class
    name."""

    class DummyPage(BasePage):
        async def dispatch(self, request: Request) -> Response:
            return Response('ok')

    page = DummyPage()
    assert page.label == 'Dummy'


def test_automatically_generates_plural_label(create_test_app: CreateTestAppFactory) -> None:
    """BasePage should automatically generate plural label form based on
    label."""

    class DummyPage(BasePage):
        async def dispatch(self, request: Request) -> Response:
            return Response('ok')

    page = DummyPage()
    assert page.label_plural == 'Dummies'


def test_automatically_generates_page_title(create_test_app: CreateTestAppFactory) -> None:
    """BasePage should automatically generate page title based on label."""

    class DummyPage(BasePage):
        async def dispatch(self, request: Request) -> Response:
            return Response('ok')

    page = DummyPage()
    assert page.page_title == 'Dummy'


def test_automatically_generates_path_name(create_test_app: CreateTestAppFactory) -> None:
    """BasePage should automatically generate path name using slug."""

    class DummyPage(BasePage):
        async def dispatch(self, request: Request) -> Response:
            return Response('ok')

    page = DummyPage()
    assert page.get_path_name() == 'app.pages.dummy'


def test_automatically_generates_url(create_test_app: CreateTestAppFactory) -> None:
    """BasePage should automatically generate URL using slug."""

    class DummyPage(BasePage):
        async def dispatch(self, request: Request) -> Response:
            return Response(DummyPage.generate_url(request))

    client = TestClient(create_test_app(pages=[DummyPage()]))
    response = client.get('/admin/dummy')
    assert response.text == 'http://testserver/admin/dummy'


def test_render_to_response(create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path) -> None:
    """BasePage should provide render_to_response shortcut."""

    class DummyPage(BasePage):
        async def dispatch(self, request: Request) -> Response:
            return self.render_to_response(request, 'sample.html')

    (extra_template_dir / 'sample.html').write_text('hello')

    client = TestClient(create_test_app(pages=[DummyPage()]))
    response = client.get('/admin/dummy')
    assert response.status_code == 200
    assert response.text == 'hello'


def test_redirect_to_path(create_test_app: CreateTestAppFactory) -> None:
    """BasePage should provide redirect_to_path shortcut."""

    class DummyPage(BasePage):
        async def dispatch(self, request: Request) -> Response:
            return self.redirect_to_path(request, self.get_path_name())

    client = TestClient(create_test_app(pages=[DummyPage()]))
    response = client.get('/admin/dummy', allow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'http://testserver/admin/dummy'


def test_redirect_to_url(create_test_app: CreateTestAppFactory) -> None:
    """BasePage should provide redirect_to shortcut."""

    class DummyPage(BasePage):
        async def dispatch(self, request: Request) -> Response:
            return self.redirect_to('http://example.com')

    client = TestClient(create_test_app(pages=[DummyPage()]))
    response = client.get('/admin/dummy', allow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'http://example.com'


def test_redirect_to_self(create_test_app: CreateTestAppFactory) -> None:
    """BasePage should provide redirect_to_self shortcut that redirects back to
    this page."""

    class DummyPage(BasePage):
        async def dispatch(self, request: Request) -> Response:
            return self.redirect_to_self(request)

    client = TestClient(create_test_app(pages=[DummyPage()]))
    response = client.get('/admin/dummy', allow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'http://testserver/admin/dummy'
