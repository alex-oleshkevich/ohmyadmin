from starlette.datastructures import URL
from starlette.requests import Request

from ohmyadmin.templating import media_url, static_url, url_matches
from tests.conftest import RequestFactory


def test_static_url(http_request: Request) -> None:
    assert static_url(http_request, "main.js").path == "/admin/static/main.js"


def test_static_url_address_timestamp(http_request: Request) -> None:
    http_request.app.debug = True
    url = static_url(http_request, "main.js")
    assert "_ts" in url.query


def test_static_url_redirects_http(http_request: Request) -> None:
    assert str(static_url(http_request, "http://image.server")) == "http://image.server"
    assert str(static_url(http_request, "https://image.server")) == "https://image.server"


def test_media_url(http_request: Request) -> None:
    assert str(media_url(http_request, "video.webp")) == "/admin/media/video.webp"


def test_media_url_redirects_http(http_request: Request) -> None:
    assert str(media_url(http_request, "http://image.server")) == "http://image.server"
    assert str(media_url(http_request, "https://image.server")) == "https://image.server"


def test_url_matches(request_f: RequestFactory) -> None:
    request = request_f("get", "/admin/welcome")
    assert url_matches(request, "/admin")
    assert url_matches(request, URL("/admin"))
    assert url_matches(request, "/admin/welcome")
    assert url_matches(request, URL("/admin/welcome"))
    assert not url_matches(request, "/admin/welcome/nested")
    assert not url_matches(request, URL("/admin/welcome/nested"))
    assert not url_matches(request, "/admin/login")
    assert not url_matches(request, URL("/admin/login"))
