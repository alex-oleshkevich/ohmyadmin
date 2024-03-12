import typing

from starlette.requests import Request

from ohmyadmin.components.layout import Column, Grid
from ohmyadmin.components.base import Component
from ohmyadmin.components.text import Container, Placeholder, Text

T = typing.TypeVar("T")


class DetailView(Component, typing.Generic[T]):
    """Component renders model detail page."""

    template_name = "ohmyadmin/components/display/display_view.html"

    def __init__(self, model: T) -> None:
        self.model = model

    def build(self, request: Request) -> Component:
        return Placeholder(message="This view does not define any content.")


class ModelField(Component, typing.Generic[T]):
    """Component renders model field value."""

    template_name = "ohmyadmin/components/display/model_field.html"

    def __init__(self, label: str, value: Component) -> None:
        self.label = label
        self.value = value

    def build(self, request: Request) -> Component:
        return Grid(
            columns=12,
            children=[
                Column(children=[Text(self.label)], colspan=3),
                Column(children=[Container(child=self.value)], colspan=9),
            ],
        )
