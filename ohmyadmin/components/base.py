from __future__ import annotations

import abc
import enum
import typing

from starlette.requests import Request

from ohmyadmin.templating import render_to_string


class BaseComponent(abc.ABC):
    @abc.abstractmethod
    def render(self, request: Request) -> str:
        raise NotImplementedError()


class Component(BaseComponent):
    template_name: str = ""

    def render(self, request: Request) -> str:
        assert self.template_name, f"Component {self.__class__} does not define template."
        return render_to_string(request, self.template_name, {"component": self})


class ComposeComponent(Component):
    template_name: str = "ohmyadmin/components/compose.html"

    @abc.abstractmethod
    def compose(self, request: Request) -> Component:
        raise NotImplementedError()

    def render(self, request: Request) -> str:
        assert self.template_name, f"Component {self.__class__} does not define template."
        child = self.compose(request)
        return render_to_string(request, self.template_name, {"component": child, "self": self})


ComponentBuilder = typing.Callable[[], Component]


class Builder(ComposeComponent):
    def __init__(self, builder: ComponentBuilder) -> None:
        self.builder = builder

    def compose(self, request: Request) -> Component:
        return self.builder()


class When(ComposeComponent):
    def __init__(self, expression: bool, when_true: Component, when_false: Component) -> None:
        self.expression = expression
        self.when_true = when_true
        self.when_false = when_false

    def compose(self, request: Request) -> Component:
        return self.when_true if self.expression else self.when_false


class AvatarSize(enum.StrEnum):
    SMALL = "sm"
    MEDIUM = "md"
    LARGE = "lg"
    XLARGE = "xl"


class AvatarStatus(enum.StrEnum):
    NONE = "none"
    RED = "red"
    GREEN = "green"


class Avatar(Component):
    template_name = "ohmyadmin/components/avatar.html"

    def __init__(
        self,
        image_url: str,
        text: str = "",
        size: AvatarSize = AvatarSize.MEDIUM,
        status_icon: AvatarStatus = AvatarStatus,
    ) -> None:
        self.size = size
        self.text = text
        self.image_url = image_url
        self.status_icon = status_icon
