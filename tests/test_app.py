from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.testclient import TestClient

from ohmyadmin.app import OhMyAdmin
from ohmyadmin.menu import MenuLink
from ohmyadmin.pages.page import Page
from tests.conftest import CreateTestAppFactory


def test_url_for(create_test_app: CreateTestAppFactory) -> None:
    class ExamplePage(Page):
        async def get(self, request: Request) -> Response:
            return PlainTextResponse(request.state.admin.url_for(request, 'ohmyadmin.login'))

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert client.get('/admin/example').text == 'http://testserver/admin/login'


def test_static_url(create_test_app: CreateTestAppFactory) -> None:
    class ExamplePage(Page):
        async def get(self, request: Request) -> Response:
            return PlainTextResponse(request.state.admin.static_url(request, 'js/asset.js'))

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    # url generator appends timestamp to reset browser cache
    # we have to check if the url starts with the expected one
    assert client.get('/admin/example').text.startswith('http://testserver/admin/static/js/asset.js')


def test_media_url_for_upload(create_test_app: CreateTestAppFactory) -> None:
    class ExamplePage(Page):
        async def get(self, request: Request) -> Response:
            return PlainTextResponse(request.state.admin.media_url(request, 'uploads/file.txt'))

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    # url generator appends timestamp to reset browser cache
    # we have to check if the url starts with the expected one
    assert client.get('/admin/example').text == 'http://testserver/admin/media/uploads/file.txt'


def test_media_url_for_http_url(create_test_app: CreateTestAppFactory) -> None:
    """When media file is a URL then admin must redirect to FileServer app that."""

    class ExamplePage(Page):
        async def get(self, request: Request) -> Response:
            return PlainTextResponse(request.state.admin.media_url(request, 'http://example.com/image.gif'))

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert client.get('/admin/example').text == 'http://example.com/image.gif'


def test_media_url_for_https_url(create_test_app: CreateTestAppFactory) -> None:
    """When media file is a URL then admin must redirect to FileServer app that."""

    class ExamplePage(Page):
        async def get(self, request: Request) -> Response:
            return PlainTextResponse(request.state.admin.media_url(request, 'https://example.com/image.gif'))

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert client.get('/admin/example').text == 'https://example.com/image.gif'


def test_generates_routes_to_pages(create_test_app: CreateTestAppFactory) -> None:
    """Admin should generate routes to pages."""

    class ExamplePage(Page):
        pass

    class Example2Page(Page):
        slug = 'other-example'

        async def get(self, request: Request) -> Response:
            return PlainTextResponse('ok')

    app = create_test_app([ExamplePage(), Example2Page()])
    client = TestClient(app)

    assert client.get('/admin/example').is_success
    assert client.get('/admin/other-example').is_success


def test_provides_index_view(create_test_app: CreateTestAppFactory) -> None:
    """Admin should display index page stub."""
    app = create_test_app([])
    client = TestClient(app)

    assert 'Welcome' in client.get('/admin').text


def test_renders_user_menu(create_test_app: CreateTestAppFactory) -> None:
    """
    Users should be able to configure user menu.

    These menu items later rendered in a dropdown.
    """
    app = create_test_app(user_menu=[MenuLink(text='User Menu Item', url='/')])
    client = TestClient(app)

    assert 'User Menu Item' in client.get('/admin').text


def test_renders_main_menu(create_test_app: CreateTestAppFactory) -> None:
    """Admin should render main navigation."""

    class ExamplePage(Page):
        slug = 'example'
        label = 'Main Menu Item'

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert 'Main Menu Item' in client.get('/admin/example').text


def test_exposes_self_to_state(create_test_app: CreateTestAppFactory) -> None:
    """Admin should add self instance to request.state."""

    class ExamplePage(Page):
        async def get(self, request: Request) -> Response:
            return PlainTextResponse(str(isinstance(request.state.admin, OhMyAdmin)))

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert client.get('/admin/example').text == 'True'
