import typing

from starlette.requests import Request

from ohmyadmin.components import Component, Placeholder

M = typing.TypeVar("M")


class IndexView(Component, typing.Generic[M]):
    template_name = "ohmyadmin/components/forms/form_view.html"

    def __init__(self, models: typing.Iterable[M]) -> None:
        self.models = models

    def build(self, request: Request) -> Component:
        return Placeholder(message="This view does not define any content.")
