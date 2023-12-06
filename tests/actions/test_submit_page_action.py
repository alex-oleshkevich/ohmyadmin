from starlette.requests import Request

from ohmyadmin.actions import Submit
from ohmyadmin.testing import MarkupSelector


def test_action_renders_template(http_request: Request) -> None:
    page = Submit(label="Item")
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_text("button") == "Item"
    assert selector.get_attribute("button", "type") == "submit"
    assert selector.has_class("button", "btn-default")
    assert not selector.has_node("button svg")


def test_action_renders_template_with_variant(http_request: Request) -> None:
    page = Submit(label="Item", variant="danger")
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_class("button", "btn-danger")


def test_action_renders_template_with_html_attrs(http_request: Request) -> None:
    page = Submit(label="Item", html_attrs={"id": "click"})
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_attribute("button", "id") == "click"


def test_action_renders_template_with_name(http_request: Request) -> None:
    page = Submit(label="Item", name="redirect")
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_attribute("button", "name") == "redirect"


def test_action_renders_template_with_type(http_request: Request) -> None:
    page = Submit(label="Item", type="button")
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_attribute("button", "type") == "button"
