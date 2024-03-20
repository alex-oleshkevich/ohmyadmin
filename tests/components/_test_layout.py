from starlette.requests import Request

from ohmyadmin import components
from ohmyadmin.components import layout
from ohmyadmin.testing import MarkupSelector


class Child(components.Component):
    def render(self, request: Request) -> str:
        return "CHILD"


def test_column(http_get: Request) -> None:
    component = layout.Column(children=[Child()], gap=5, colspan=5)
    html = component.render(http_get)
    selector = MarkupSelector(html)
    assert selector.find_node(".column-layout")
    assert selector.has_class(".column-layout", "gap-5", "col-span-5")
    assert selector.has_text(".column-layout", "CHILD")


def test_grid(http_get: Request) -> None:
    component = layout.Grid(children=[Child()], columns=5, gap=5, colspan=5)
    html = component.render(http_get)
    selector = MarkupSelector(html)
    assert selector.find_node(".grid-layout")
    assert selector.has_class(".grid-layout", "gap-5", "col-span-5", "grid-cols-5")
    assert selector.has_text(".grid-layout", "CHILD")
