from __future__ import annotations

import abc
import enum
import typing

from starlette.datastructures import URL
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin.components.base import Component
from ohmyadmin.routing import LazyURL, resolve_url, URLProvider, URLType

T = typing.TypeVar("T")


class Text(Component):
    template_name = "ohmyadmin/components/text/text.html"

    def __init__(self, text: str = "", empty_value: str = "-") -> None:
        self.text = text or empty_value
        self.empty_value = empty_value


class Link(Component):
    template_name = "ohmyadmin/components/text/link.html"

    def __init__(
        self,
        url: URLType | URLProvider | None = None,
        *,
        text: str,
        target: typing.Literal["", "_blank"] = "",
    ) -> None:
        self.text = text
        self.target = target
        self.url = URL(url) if isinstance(url, str) else url

        if hasattr(url, "url_name"):
            self.url = LazyURL(url)

    def get_url(self, request: Request) -> URL:
        return resolve_url(request, self.url)


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


class ButtonVariant(enum.StrEnum):
    DEFAULT = "default"
    ACCENT = "accent"
    PRIMARY = "primary"
    DANGER = "danger"
    ICON = "icon"
    TEXT = "text"


class Button(Component):
    template_name: str = "ohmyadmin/components/button.html"

    def __init__(
        self,
        text: str | None = None,
        icon: str | None = None,
        variant: ButtonVariant = ButtonVariant.DEFAULT,
    ) -> None:
        assert text or icon, "Must provide either text or icon."
        self.text = text
        self.icon = icon
        self.variant = variant


class DropdownMenuItem(Component, abc.ABC):
    template_name = "ohmyadmin/components/dropdown_menu_item.html"

    def __init__(self, child: Component, leading: Component | None = None, trailing: Component | None = None) -> None:
        self.child = child
        self.leading = leading
        self.trailing = trailing


class DropdownMenuLink(DropdownMenuItem):
    template_name = "ohmyadmin/components/dropdown_menu_link.html"

    def __init__(
        self, url: URLType, child: Component, leading: Component | None = None, trailing: Component | None = None
    ) -> None:
        self.url = url
        super().__init__(child, leading, trailing)

    def resolve(self, request: Request) -> URL:
        return resolve_url(request, self.url)


class DropdownMenu(Component):
    template_name = "ohmyadmin/components/dropdown_menu.html"

    def __init__(
        self,
        trigger: Component,
        items: typing.Iterable[Component],
    ) -> None:
        self.trigger = trigger
        self.items = items
