from starlette.requests import Request
from unittest import mock

from ohmyadmin.actions import Callback
from ohmyadmin.testing import MarkupSelector


def test_action_renders_template(http_request: Request) -> None:
    page = Callback(slug="callback", label="Item", callback=mock.MagicMock())
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_text("button") == "Item"
    assert selector.get_attribute("button", "type") == "button"
    assert selector.has_class("button", "btn-default")
    assert (
        selector.get_attribute("button", "hx-get")
        == "http://testserver/admin/?_action=callback"
    )
    assert not selector.has_node("button svg")


def test_action_renders_template_with_icon(http_request: Request) -> None:
    page = Callback(
        slug="callback", label="Item", callback=mock.MagicMock(), icon="plus"
    )
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_node("button svg")


def test_action_renders_template_with_variant(http_request: Request) -> None:
    page = Callback(
        slug="callback", label="Item", callback=mock.MagicMock(), variant="danger"
    )
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_class("button", "btn-danger")


def test_action_renders_template_with_confirmation(http_request: Request) -> None:
    page = Callback(
        slug="callback", label="Item", callback=mock.MagicMock(), confirmation="Run?"
    )
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_attribute("button", "hx-confirm") == "Run?"


def test_action_renders_template_with_http_method(http_request: Request) -> None:
    page = Callback(
        slug="callback", label="Item", callback=mock.MagicMock(), http_method="post"
    )
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_attribute("button", "hx-post")


def test_action_renders_template_with_hx_target(http_request: Request) -> None:
    page = Callback(
        slug="callback", label="Item", callback=mock.MagicMock(), hx_target="modals"
    )
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_attribute("button", "hx-target") == "modals"


async def test_action_dispatches_callback(http_request: Request) -> None:
    fn = mock.AsyncMock()
    page = Callback(slug="callback", label="Item", callback=fn, hx_target="modals")
    await page.dispatch(http_request)
    fn.assert_called_once_with(http_request)
