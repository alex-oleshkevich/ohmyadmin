from __future__ import annotations

import enum
import typing

from starlette.datastructures import URL
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin import formatters
from ohmyadmin.components.base import Component
from ohmyadmin.routing import LazyURL, URLProvider

T = typing.TypeVar("T")


class Text(Component):
    template_name = "ohmyadmin/components/text/text.html"

    def __init__(
        self, text: str = "", empty_value: str = "-", formatter: formatters.ValueFormatter | None = None
    ) -> None:
        self.text = text or empty_value
        self.formatter = formatter
        self.empty_value = empty_value

    def build(self, request: Request) -> Component:
        text = (
            self.formatter(request, self.text)
            if (self.formatter and self.text != self.empty_value and self.text)
            else self.text
        )
        return Text(text=text)


class Placeholder(Component):
    template_name = "ohmyadmin/components/text/placeholder.html"

    def __init__(self, message: str) -> None:
        self.message = message


class Container(Component):
    template_name = "ohmyadmin/components/container.html"

    def __init__(self, child: Component, colspan: int = 12) -> None:
        self.child = child
        self.colspan = colspan


class Link(Component):
    template_name = "ohmyadmin/components/text/link.html"

    def __init__(
        self,
        url: str | URL | LazyURL | URLProvider | None = None,
        *,
        text: str,
        target: typing.Literal["", "_blank"] = "",
        builder: typing.Callable[[], str | URL] = None,
    ) -> None:
        self.text = text
        self.target = target
        self.url = URL(url) if isinstance(url, str) else url
        self.builder = builder

        if hasattr(url, "url_name"):
            self.url = LazyURL(url)

    def get_url(self, request: Request) -> URL:
        if isinstance(self.url, URL):
            return self.url

        if isinstance(self.url, LazyURL):
            return self.url.resolve(request)

        return URL(self.builder())


class BadgeColor(enum.StrEnum):
    DEFAULT = "default"
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    INDIGO = "indigo"
    PURPLE = "purple"
    PINK = "pink"
    ROSE = "rose"


class Badge(Component, typing.Generic[T]):
    template_name = "ohmyadmin/components/badge.html"

    def __init__(self, value: T, colors: typing.Mapping[T, BadgeColor]) -> None:
        self.value = value
        self.color = colors.get(value, BadgeColor.DEFAULT)


class BoolValue(Component):
    template_name = "ohmyadmin/components/boolean.html"

    def __init__(
        self,
        value: bool,
        as_text: bool = True,
        show_text: bool = True,
        true_text: str = _("Yes"),
        false_text: str = _("No"),
    ) -> None:
        self.value = value
        self.as_text = as_text
        self.show_text = show_text
        self.true_text = true_text
        self.false_text = false_text


class Image(Component):
    template_name: str = "ohmyadmin/components/image.html"

    def __init__(self, src: str, alt: str = "") -> None:
        self.src = src
        self.alt = alt
