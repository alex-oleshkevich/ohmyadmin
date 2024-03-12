from starlette.requests import Request

from ohmyadmin.components.base import Component


class When(Component):
    template_name = "ohmyadmin/components/when.html"

    def __init__(self, expression: bool, when_true: Component, when_false: Component) -> None:
        self.expression = expression
        self.when_true = when_true
        self.when_false = when_false

    def build(self, request: Request) -> Component:
        return self.when_true if self.expression else self.when_false
