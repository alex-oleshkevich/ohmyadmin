import typing

from starlette.requests import Request

from ohmyadmin import formatters
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

    def __init__(
        self,
        label: str,
        value: T = None,
        formatter: formatters.ValueFormatter = formatters.Auto(),
        value_builder: typing.Callable[[T], Component] | None = None,
        empty_value: str = "-",
    ) -> None:
        self.label = label
        self.value = value
        self.formatter = formatter
        self.empty_value = empty_value
        self.value_builder = value_builder

    def build(self, request: Request) -> Component:
        formatted_value = self.formatter(request, self.value) if self.value is not None else self.empty_value
        value = Text(formatted_value)
        if self.value_builder:
            value = self.value_builder(formatted_value)

        return Grid(
            columns=12,
            children=[
                Column(children=[Text(self.label)], colspan=3),
                Column(children=[Container(child=value)], colspan=9),
            ],
        )
