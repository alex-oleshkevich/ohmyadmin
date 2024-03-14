from __future__ import annotations

import abc
import enum
import typing

from markupsafe import Markup
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


class Placeholder(Component):
    template_name = "ohmyadmin/components/text/placeholder.html"

    def __init__(self, message: str) -> None:
        self.message = message


class Container(Component):
    template_name = "ohmyadmin/components/container.html"

    def __init__(self, child: Component, colspan: int = 12) -> None:
        self.child = child
        self.colspan = colspan


class Column(Component):
    template_name: str = "ohmyadmin/components/layout/column.html"

    def __init__(
        self,
        children: typing.Iterable[Component],
        gap: int = 0,
        colspan: int = 12,
    ) -> None:
        self.gap = gap
        self.colspan = colspan
        self.children = children


class AxisAlign(enum.StrEnum):
    START = "start"
    CENTER = "center"
    END = "end"


class Row(Component):
    template_name: str = "ohmyadmin/components/layout/row.html"

    def __init__(
        self,
        children: typing.Iterable[Component],
        align: AxisAlign = AxisAlign.START,
        gap: int = 0,
        colspan: int = 12,
    ) -> None:
        self.gap = gap
        self.align = align
        self.colspan = colspan
        self.children = children


class Grid(Component):
    template_name: str = "ohmyadmin/components/layout/grid.html"

    def __init__(
        self,
        children: typing.Iterable[Component],
        columns: int = 12,
        gap: int = 5,
        colspan: int = 12,
    ) -> None:
        self.gap = gap
        self.colspan = colspan
        self.columns = columns
        self.children = children


class Group(Component):
    template_name: str = "ohmyadmin/components/group.html"

    def __init__(
        self,
        children: typing.Iterable[Component],
        label: str = "",
        description: str = "",
        colspan: int = 12,
        gap: int = 2,
    ) -> None:
        self.gap = gap
        self.label = label
        self.colspan = colspan
        self.children = children
        self.description = description


class HTML(Component):
    def __init__(self, markup: str) -> None:
        self.markup = markup

    def render(self, request: Request) -> str:
        return Markup(self.markup)


class Empty(ComposeComponent):
    def compose(self, request: Request) -> Component:
        return HTML("")


class PageToolbar(ComposeComponent):
    def __init__(self, builder: typing.Callable[[Request], typing.Iterable[Component]] | None = None) -> None:
        self.builder = builder

    def build(self, request: Request) -> typing.Iterable[Component]:
        return self.builder(request)

    def compose(self, request: Request) -> Component:
        if self.builder:
            return Row(children=self.build(request), gap=2)
        return Empty()
