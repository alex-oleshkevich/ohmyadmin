import httpx
import pytest

from ohmyadmin.testing import MarkupSelector, NodeNotFoundError


def test_from_response() -> None:
    response = httpx.Response(200, content="<span>hello</span>")
    selector = MarkupSelector.from_response(response)
    assert isinstance(selector, MarkupSelector)


def test_find_node() -> None:
    selector = MarkupSelector("<div><span></span></div>")
    node = selector.find_node("span")
    assert node
    assert node.name == "span"


def test_find_node_or_raise() -> None:
    selector = MarkupSelector("<div><span></span></div>")
    node = selector.find_node_or_raise("span")
    assert node
    assert node.name == "span"

    with pytest.raises(NodeNotFoundError):
        selector.find_node_or_raise("img")


def test_get_attribute() -> None:
    selector = MarkupSelector('<div class="red blue" title="div tag"></div>')
    assert selector.get_attribute("div", "class") == "red blue"
    assert selector.get_attribute("div", "title") == "div tag"


def test_has_attribute() -> None:
    selector = MarkupSelector('<div class="red blue" title="div tag"></div>')
    assert selector.has_attribute("div", "title")
    assert not selector.has_attribute("div", "id")


def test_match_attribute() -> None:
    selector = MarkupSelector('<div class="red blue" title="div tag"></div>')
    assert selector.match_attribute("div", "title", "div tag")
    assert not selector.match_attribute("div", "title", "invalid")


def test_get_classes() -> None:
    selector = MarkupSelector('<div class="red blue"></div>')
    assert selector.get_classes("div") == ["red", "blue"]


def test_has_class() -> None:
    selector = MarkupSelector('<div class="red blue"></div>')
    assert selector.has_class("div", "red") is True
    assert selector.has_class("div", "red", "blue") is True
    assert selector.has_class("div", "green") is False
    assert selector.has_class("div", "green", "red") is False


def test_get_styles() -> None:
    selector = MarkupSelector('<div style="color: red; font-size: 12px"></div>')
    assert selector.get_styles("div") == {"color": "red", "font-size": "12px"}

    selector = MarkupSelector("<div>")
    assert selector.get_styles("div") == {}


def test_get_style() -> None:
    selector = MarkupSelector('<div style="color: red"></div>')
    assert selector.get_style("div", "color") == "red"
    assert selector.get_style("div", "font-size") == ""


def test_has_style() -> None:
    selector = MarkupSelector('<div style="color: red"></div>')
    assert selector.has_style("div", "color")
    assert not selector.get_style("div", "font-size")


def test_has_node() -> None:
    selector = MarkupSelector("<div><span></span></div>")
    assert selector.has_node("div")
    assert selector.has_node("span")
    assert selector.has_node("div span")


def test_count() -> None:
    selector = MarkupSelector("<div><span></span><span></span></div>")
    assert selector.count("div") == 1
    assert selector.count("span") == 2
    assert selector.count("div span") == 2


def test_get_text() -> None:
    selector = MarkupSelector("<div>div text<span>span text</span></div>")
    assert selector.get_text("div") == "div textspan text"
    assert selector.get_text("span") == "span text"
    assert selector.get_text("img") == ""
