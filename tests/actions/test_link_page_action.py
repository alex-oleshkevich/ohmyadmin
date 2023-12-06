from starlette.requests import Request

from ohmyadmin.actions import Link
from ohmyadmin.helpers import LazyURL
from ohmyadmin.testing import MarkupSelector


def test_action_renders_template(http_request: Request) -> None:
    page = Link(label="Item", url="/")
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_text("a") == "Item"
    assert selector.get_attribute("a", "href") == "/"
    assert selector.has_class("a", "btn-link")
    assert not selector.has_node("a svg")


def test_action_renders_template_with_custom_button_type(http_request: Request) -> None:
    page = Link(label="Item", url="/", variant="text")
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_class("a", "btn-text")


def test_action_renders_template_with_icon(http_request: Request) -> None:
    page = Link(label="Item", url="/", icon="plus")
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.has_node("a svg")


def test_action_renders_template_with_lazy_url(http_request: Request) -> None:
    page = Link(label="Item", url=LazyURL(path_name="posts", path_params={"id": "100"}))
    content = page.render(http_request)
    selector = MarkupSelector(content)
    assert selector.get_attribute("a", "href") == "http://testserver/admin/posts/100"
