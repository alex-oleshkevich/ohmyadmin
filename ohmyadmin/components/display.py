import typing

from starlette.requests import Request

from ohmyadmin.components.base import Component, ComposeComponent
from ohmyadmin.components.base import Column, Grid
from ohmyadmin.components.text import Text
from ohmyadmin.components import Container, Placeholder

T = typing.TypeVar("T")


class DetailView(ComposeComponent, typing.Generic[T]):
    """Component renders model detail page."""

    def __init__(self, model: T) -> None:
        self.model = model

    def compose(self, request: Request) -> Component:
        return Placeholder(message="This view does not define any content.")


class ModelField(ComposeComponent, typing.Generic[T]):
    """Component renders model field value."""

    def __init__(self, label: str, value: Component) -> None:
        self.label = label
        self.value = value

    def compose(self, request: Request) -> Component:
        return Grid(
            columns=12,
            children=[
                Column(children=[Text(self.label)], colspan=3),
                Column(children=[Container(child=self.value)], colspan=9),
            ],
        )
