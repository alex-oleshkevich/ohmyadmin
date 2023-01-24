import pathlib
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.testclient import TestClient

from ohmyadmin.pages.page import TemplatePage
from tests.conftest import CreateTestAppFactory


def test_loads_templates_from_user_directory(
    create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path
) -> None:
    """Users can provide their own template directory and that directory must
    have the highest precedence to make template override possible."""

    (extra_template_dir / 'ohmyadmin').mkdir()
    (extra_template_dir / 'ohmyadmin/index.html').write_text('from custom index')

    class ExamplePage(TemplatePage):
        async def get(self, request: Request) -> Response:
            template = request.state.admin.jinja_env.get_template('ohmyadmin/index.html')
            return PlainTextResponse(template.render())

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert client.get('/admin/example').text == 'from custom index'


def test_renders_template_to_string(create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path) -> None:
    """Admin should render a template to string using .render_to_string
    method."""

    (extra_template_dir / 'sample.txt').write_text('hello {{ value }}')

    class ExamplePage(TemplatePage):
        async def get(self, request: Request) -> Response:
            return PlainTextResponse(request.state.admin.render_to_string(request, 'sample.txt', {'value': 'world'}))

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert client.get('/admin/example').text == 'hello world'


def test_renders_to_string_has_context(create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path) -> None:
    """Admin should expose global request-aware template variables when
    rendering templates using render_to_string."""

    (extra_template_dir / 'sample.txt').write_text(
        "'request' if request is not none else '' \n"
        "'url' if url is not none else '' \n"
        "'static_url' if static_url is not none else '' \n"
        "'media_url' if media_url is not none else '' \n"
        "'flash_messages' if flash_messages is not none else '' \n"
    )

    class ExamplePage(TemplatePage):
        async def get(self, request: Request) -> Response:
            return PlainTextResponse(request.state.admin.render_to_string(request, 'sample.txt'))

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    response = client.get('/admin/example')
    assert 'request' in response.text
    assert 'url' in response.text
    assert 'static_url' in response.text
    assert 'media_url' in response.text
    assert 'flash_messages' in response.text


def test_renders_to_response_has_context(
    create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path
) -> None:
    """Admin should expose global request-aware template variables when
    rendering templates using render_to_response."""

    (extra_template_dir / 'sample.txt').write_text(
        "'request' if request is not none else '' \n"
        "'url' if url is not none else '' \n"
        "'static_url' if static_url is not none else '' \n"
        "'media_url' if media_url is not none else '' \n"
        "'flash_messages' if flash_messages is not none else '' \n"
    )

    class ExamplePage(TemplatePage):
        async def get(self, request: Request) -> Response:
            return request.state.admin.render_to_response(request, 'sample.txt')

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    response = client.get('/admin/example')
    assert 'request' in response.text
    assert 'url' in response.text
    assert 'static_url' in response.text
    assert 'media_url' in response.text
    assert 'flash_messages' in response.text


def test_renders_template_to_response(create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path) -> None:
    """Admin should render a template to HTTP response using .render_to_response
    method."""

    (extra_template_dir / 'sample.txt').write_text('hello {{ value }}')

    class ExamplePage(TemplatePage):
        async def get(self, request: Request) -> Response:
            return request.state.admin.render_to_response(request, 'sample.txt', {'value': 'world'})

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert client.get('/admin/example').text == 'hello world'


def test_jinja_automatically_escapes(create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path) -> None:
    """Jinja engine must escape values by default for security reasons."""

    (extra_template_dir / 'sample.txt').write_text('hello {{ value }}')

    class ExamplePage(TemplatePage):
        async def get(self, request: Request) -> Response:
            return request.state.admin.render_to_response(request, 'sample.txt', {'value': '<b>world</b>'})

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert client.get('/admin/example').text == 'hello &lt;b&gt;world&lt;/b&gt;'


def test_admin_exposes_self_to_templates(
    create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path
) -> None:
    """Admin instance should make self available globally in templates."""

    (extra_template_dir / 'sample.txt').write_text('hello {{ admin.title }}')

    class ExamplePage(TemplatePage):
        async def get(self, request: Request) -> Response:
            return request.state.admin.render_to_response(request, 'sample.txt')

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert client.get('/admin/example').text == 'hello Oh My Admin!'


def test_admin_exposes_tabler_icons_to_templates(
    create_test_app: CreateTestAppFactory, extra_template_dir: pathlib.Path
) -> None:
    """Admin instance should expose Table icon set globally in templates."""

    (extra_template_dir / 'sample.txt').write_text('{{tabler_icon("plus")}}')

    class ExamplePage(TemplatePage):
        async def get(self, request: Request) -> Response:
            return request.state.admin.render_to_response(request, 'sample.txt')

    app = create_test_app([ExamplePage()])
    client = TestClient(app)

    assert 'svg' in client.get('/admin/example').text
