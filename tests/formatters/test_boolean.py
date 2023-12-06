from starlette.requests import Request

from ohmyadmin.formatters import BoolFormatter
from ohmyadmin.testing import MarkupSelector


def test_boolean_icons_positive(http_request: Request) -> None:
    formatter = BoolFormatter()
    content = formatter.format(http_request, True)
    selector = MarkupSelector(content)
    assert selector.has_node('[data-test="bool-true"]')
    assert selector.has_node("svg")


def test_boolean_icons_negative(http_request: Request) -> None:
    formatter = BoolFormatter()
    content = formatter.format(http_request, False)
    selector = MarkupSelector(content)
    assert selector.has_node('[data-test="bool-false"]')
    assert selector.has_node("svg")


def test_boolean_text_positive(http_request: Request) -> None:
    formatter = BoolFormatter(as_text=True)
    content = formatter.format(http_request, True)
    selector = MarkupSelector(content)
    assert selector.has_node('[data-test="bool-true"]')
    assert not selector.has_node("svg")
    assert selector.get_text(".badge") == "Yes"


def test_boolean_text_negative(http_request: Request) -> None:
    formatter = BoolFormatter(as_text=True)
    content = formatter.format(http_request, False)
    selector = MarkupSelector(content)
    assert selector.has_node('[data-test="bool-false"]')
    assert not selector.has_node("svg")
    assert selector.get_text(".badge") == "No"


def test_boolean_custom_text_positive(http_request: Request) -> None:
    formatter = BoolFormatter(as_text=True, true_text="Good")
    content = formatter.format(http_request, True)
    selector = MarkupSelector(content)
    assert selector.has_node('[data-test="bool-true"]')
    assert not selector.has_node("svg")
    assert selector.get_text(".badge") == "Good"


def test_boolean_custom_text_negative(http_request: Request) -> None:
    formatter = BoolFormatter(as_text=True, false_text="Bad")
    content = formatter.format(http_request, False)
    selector = MarkupSelector(content)
    assert selector.has_node('[data-test="bool-false"]')
    assert not selector.has_node("svg")
    assert selector.get_text(".badge") == "Bad"
