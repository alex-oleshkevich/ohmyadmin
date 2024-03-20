import pathlib

import pytest
from starlette.requests import Request

from ohmyadmin.components import Builder, Component, ComposeComponent, When


class WorldComponent(Component):
    template_name = "world.html"


class HelloComponent(Component):
    template_name = "hello.html"

    def __init__(self, child: Component) -> None:
        self.child = child


class TwoComponents(ComposeComponent):
    def compose(self, request: Request) -> Component:
        return HelloComponent(child=WorldComponent())


def test_component(template_dir: pathlib.Path, request: Request) -> None:
    (template_dir / "world.html").write_text("world")
    component = WorldComponent()
    assert component.render(request) == "world"


def test_compose_component(template_dir: pathlib.Path, request: Request) -> None:
    (template_dir / "world.html").write_text("world")
    (template_dir / "hello.html").write_text(
        "{%- import 'ohmyadmin/components.html' as components -%}"
        "hello {{ components.render_component(request, component.child) }}"
    )
    component = TwoComponents()
    assert str(component.render(request)) == "hello world"


def test_builder(template_dir: pathlib.Path, request: Request) -> None:
    (template_dir / "world.html").write_text("world")
    component = Builder(builder=lambda: WorldComponent())
    assert component.render(request) == "world"


@pytest.mark.parametrize(
    "expression, expected",
    (
        (True, "world"),
        (False, "hello world"),
    ),
)
def test_when(template_dir: pathlib.Path, request: Request, expression: bool, expected: str) -> None:
    (template_dir / "world.html").write_text("world")
    (template_dir / "hello.html").write_text(
        "{%- import 'ohmyadmin/components.html' as components -%}"
        "hello {{ components.render_component(request, component.child) }}"
    )
    component = When(
        expression=expression,
        when_true=WorldComponent(),
        when_false=TwoComponents(),
    )
    assert component.render(request) == expected
