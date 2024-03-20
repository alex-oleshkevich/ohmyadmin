from async_storages import FileStorage
from starlette.testclient import TestClient
from starlette_babel import switch_locale

from ohmyadmin.app import OhMyAdmin
from ohmyadmin.testing import MarkupSelector
from ohmyadmin.theme import Theme
from tests.conftest import AppFactory


def test_welcome_view(client: TestClient) -> None:
    response = client.get("/admin/")
    assert response.status_code == 200


def test_app_name(app_f: AppFactory) -> None:
    admin = OhMyAdmin(app_name="Test App")
    app = app_f(admin)
    with TestClient(app) as client:
        response = client.get("/admin")
        markup = MarkupSelector.from_response(response)
        assert markup.has_text("head title", "Test App")


def test_theme_navbar_color(app_f: AppFactory) -> None:
    admin = OhMyAdmin(theme=Theme(navbar_color="#ff0000"))
    app = app_f(admin)
    with TestClient(app) as client:
        response = client.get("/admin")
        markup = MarkupSelector.from_response(response)
        assert markup.match_attribute('head meta[name="theme-color"]', "content", "#ff0000")


def test_app_favicon(app_f: AppFactory) -> None:
    admin = OhMyAdmin(theme=Theme(icon_url="http://icon.png"))
    app = app_f(admin)
    with TestClient(app) as client:
        response = client.get("/admin")
        markup = MarkupSelector.from_response(response)
        assert markup.match_attribute('head link[rel="icon"]', "href", "http://icon.png")


def test_app_language(app_f: AppFactory) -> None:
    admin = OhMyAdmin()
    app = app_f(admin)
    with TestClient(app) as client:
        response = client.get("/admin")
        markup = MarkupSelector.from_response(response)
        assert markup.match_attribute("html", "lang", "en")

        with switch_locale("be"):
            response = client.get("/admin")
            markup = MarkupSelector.from_response(response)
            assert markup.match_attribute("html", "lang", "be")


def test_main_stylesheet(app_f: AppFactory) -> None:
    admin = OhMyAdmin()
    app = app_f(admin)
    with TestClient(app) as client:
        response = client.get("/admin")
        markup = MarkupSelector.from_response(response)
        assert markup.match_attribute(
            'head link[rel="stylesheet"]',
            "href",
            "http://testserver/admin/static/main.css",
        )


def test_main_script(app_f: AppFactory) -> None:
    admin = OhMyAdmin()
    app = app_f(admin)
    with TestClient(app) as client:
        response = client.get("/admin")
        markup = MarkupSelector.from_response(response)
        assert markup.match_attribute(
            'body script[type="module"]',
            "src",
            "http://testserver/admin/static/main.js",
        )


def test_webmanifest(app_f: AppFactory) -> None:
    admin = OhMyAdmin(
        app_name="Test App",
        theme=Theme(icon_url="http://icon.png", navbar_color="#ff0000", background_color="#00ff00"),
    )
    app = app_f(admin)
    with TestClient(app) as client:
        response = client.get("/admin/site.webmanifest")
        manifest = response.json()
        assert manifest["name"] == "Test App"
        assert manifest["short_name"] == "Test App"
        assert manifest["icons"][0]["src"] == "http://icon.png"
        assert manifest["theme_color"] == "#ff0000"
        assert manifest["background_color"] == "#00ff00"
        assert manifest["start_url"] == "http://testserver/admin/?utm_source=welcome"


def test_static_files(client: TestClient) -> None:
    response = client.get("/admin/static/icons/icon.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


async def test_media_files(client: TestClient, file_storage: FileStorage) -> None:
    await file_storage.write("text.txt", b"")
    response = client.get("/admin/media/text.txt")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
