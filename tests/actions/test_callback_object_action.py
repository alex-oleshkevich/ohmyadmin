from starlette.requests import Request
from unittest import mock

from ohmyadmin.actions import ObjectCallback
from ohmyadmin.testing import MarkupSelector
from tests.models import Post

model = Post()


def test_action_renders_template(http_request: Request) -> None:
    page = ObjectCallback(slug="callback", label="Item", callback=mock.MagicMock())
    content = page.render(http_request, model)
    selector = MarkupSelector(content)
    assert selector.get_text("button") == "Item"
    assert selector.get_attribute("button", "type") == "button"
    assert selector.has_class("button", "list-menu-item")
    assert selector.get_attribute("button", "hx-target") == "#modals"
    assert (
        selector.get_attribute("button", "hx-get")
        == "http://testserver/admin/?_object_action=callback&_ids=1"
    )
    assert not selector.has_node("button svg")


def test_action_renders_template_with_icon(http_request: Request) -> None:
    page = ObjectCallback(
        slug="callback", label="Item", callback=mock.MagicMock(), icon="plus"
    )
    content = page.render(http_request, model)
    selector = MarkupSelector(content)
    assert selector.has_node("button svg")


def test_action_renders_template_with_confirmation(http_request: Request) -> None:
    page = ObjectCallback(
        slug="callback", label="Item", callback=mock.MagicMock(), confirmation="Run?"
    )
    content = page.render(http_request, model)
    selector = MarkupSelector(content)
    assert selector.get_attribute("button", "hx-confirm") == "Run?"


def test_action_renders_template_with_dangerous_color(http_request: Request) -> None:
    page = ObjectCallback(
        slug="callback", label="Item", callback=mock.MagicMock(), dangerous=True
    )
    content = page.render(http_request, model)
    selector = MarkupSelector(content)
    assert selector.has_class("button", "danger")


def test_action_renders_template_with_http_method(http_request: Request) -> None:
    page = ObjectCallback(
        slug="callback", label="Item", callback=mock.MagicMock(), http_method="post"
    )
    content = page.render(http_request, model)
    selector = MarkupSelector(content)
    assert selector.has_attribute("button", "hx-post")


async def test_action_dispatches_callback(http_request: Request) -> None:
    fn = mock.AsyncMock()
    page = ObjectCallback(slug="callback", label="Item", callback=fn)
    await page.dispatch(http_request)
    fn.assert_called_once_with(http_request)
