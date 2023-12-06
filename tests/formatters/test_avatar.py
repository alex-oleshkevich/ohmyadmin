from starlette.requests import Request

from ohmyadmin.formatters import AvatarFormatter
from ohmyadmin.testing import MarkupSelector


def test_avatar_with_url(http_request: Request) -> None:
    formatter = AvatarFormatter()
    content = formatter.format(http_request, "http://example.com/image.jpg")
    selector = MarkupSelector(content)
    assert selector.has_node(".avatar")
    assert (
        selector.get_attribute(".avatar img", "src") == "http://example.com/image.jpg"
    )


def test_avatar_with_upload(http_request: Request) -> None:
    formatter = AvatarFormatter()
    content = formatter.format(http_request, "uploads/image.jpg")
    selector = MarkupSelector(content)
    assert selector.has_node(".avatar")
    assert (
        selector.get_attribute(".avatar img", "src")
        == "http://testserver/admin/media/uploads/image.jpg"
    )
