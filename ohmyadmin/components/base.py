from __future__ import annotations

import abc
import typing

from starlette.requests import Request

from ohmyadmin.templating import render_to_string


class BaseComponent(abc.ABC):
    @abc.abstractmethod
    def render(self, request: Request) -> str:
        raise NotImplementedError()


class Component(BaseComponent):
    template_name: str = ""

    def build(self, request: Request) -> Component:
        return self

    def render(self, request: Request) -> str:
        assert self.template_name, f"Component {self.__class__} does not define template."
        component = self.build(request)
        return render_to_string(request, component.template_name, {"component": component})


ComponentBuilder = typing.Callable[[], Component]


class Builder(Component):
    template_name = "ohmyadmin/components/builder.html"

    def __init__(self, builder: ComponentBuilder) -> None:
        self.builder = builder

    def build(self, request: Request) -> Component:
        return self.builder()
