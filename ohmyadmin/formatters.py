import datetime
import decimal
import typing

from starlette.datastructures import URL
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin.templating import render_to_string

TextAlign = typing.Literal["left", "right", "center"]
_T = typing.TypeVar("_T")


class ValueFormatter(typing.Protocol):  # pragma: no cover
    """
    Data formatter is a utility that renders object field value into a different way.

    For example, boolean can be rendered as icons or yes/no text.
    """

    def __call__(self, request: Request, value: typing.Any) -> str:
        ...


class Formatter(typing.Generic[_T]):
    template: str = "ohmyadmin/formatters/value.html"

    def format(self, request: Request, value: _T) -> str:
        return render_to_string(request, self.template, {"formatter": self, "value": value})

    def __call__(self, request: Request, value: _T) -> str:
        return self.format(request, value)


class String(Formatter[str]):
    template: str = "ohmyadmin/formatters/string.html"

    def __init__(self, *, prefix: str = "", suffix: str = "") -> None:
        self.prefix = prefix
        self.suffix = suffix


class DateTime(Formatter[datetime.datetime]):
    template: str = "ohmyadmin/formatters/datetime.html"

    def __init__(self, format: typing.Literal["short", "medium", "long", "full"] = "medium") -> None:
        self.value_format = format


class Date(Formatter[datetime.date | datetime.datetime]):
    template: str = "ohmyadmin/formatters/date.html"

    def __init__(self, format: typing.Literal["short", "medium", "long", "full"] = "medium") -> None:
        self.value_format = format


class Time(Formatter[datetime.datetime | datetime.time]):
    template: str = "ohmyadmin/formatters/time.html"

    def __init__(self, format: typing.Literal["short", "medium", "long", "full"] = "short") -> None:
        self.value_format = format


class Number(Formatter[int | float | decimal.Decimal]):
    template: str = "ohmyadmin/formatters/number.html"

    def __init__(self, *, prefix: str = "", suffix: str = "", decimals: int = 2) -> None:
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals

    def round_value(self, value: _T) -> _T:
        return round(value, self.decimals)


class Link(Formatter[str]):
    """Wraps text into a link."""

    template: str = "ohmyadmin/formatters/link.html"

    def __init__(
        self,
        text: str = "",
        url_builder: typing.Callable[[str], str] | None = None,
        protocol: typing.Literal["mailto", "tel"] | None = None,
        target: typing.Literal["_blank", ""] = "",
    ) -> None:
        self.text = text
        self.target = target
        self.protocol = protocol
        self.url_builder = url_builder

    def get_link(self, value: str) -> str:
        if self.url_builder:
            return self.url_builder(value)

        if self.protocol:
            return f"{self.protocol}:{value}"

        return value


class Callback(Formatter[typing.Any]):
    def __init__(self, callback: typing.Callable[[typing.Any], str]) -> None:
        self.callback = callback

    def format(self, request: Request, value: _T) -> str:
        return self.callback(value)


class Auto(Formatter[typing.Any]):
    def format(self, request: Request, value: typing.Any) -> str:
        if isinstance(value, datetime.datetime):
            return DateTime(format="short").format(request, value)
        if isinstance(value, datetime.date):
            return Date().format(request, value)
        if isinstance(value, datetime.time):
            return Time().format(request, value)
        if isinstance(value, (int, float, complex, decimal.Decimal)):
            return Number().format(request, value)
        if isinstance(value, str) and (value.startswith("http://") or value.startswith("https://")):
            return Link().format(request, value)

        return String().format(request, value)


class LinkFormatter(Formatter[str]):
    template: str = "ohmyadmin/formatters/link_formatter.html"

    def __init__(
        self,
        *,
        url: str | URL,
        target: typing.Literal["_blank", ""] = "",
    ) -> None:
        self.url = url
        self.target = target

    def format(self, request: Request, value: str) -> str:
        if callable(self.url):
            url = self.url(request, value)
        else:
            url = self.url

        return render_to_string(request, self.template, {"formatter": self, "value": value, "url": url})


class BoolFormatter(Formatter[bool]):
    template: str = "ohmyadmin/formatters/bool.html"

    def __init__(
        self,
        as_text: bool = False,
        true_text: str = _("Yes", domain="ohmyadmin"),
        false_text: str = _("No", domain="ohmyadmin"),
        align: typing.Literal["left", "center", "right"] = "left",
    ) -> None:
        self.true_text = true_text
        self.false_text = false_text
        self.as_text = as_text
        self.align = align


class AvatarFormatter(Formatter[str]):
    template: str = "ohmyadmin/formatters/avatar.html"


LinkFactory: typing.TypeAlias = typing.Callable[[Request, typing.Any], URL]

BadgeColor: typing.TypeAlias = typing.Literal["gray", "red", "yellow", "green", "blue", "indigo", "purple", "pink"]


class BadgeFormatter(Formatter[str | int]):
    template: str = "ohmyadmin/formatters/badge.html"

    def __init__(self, *, color_map: dict[str | int, BadgeColor]) -> None:
        self.color_map = color_map or {}

    def format(self, request: Request, value: str | int) -> str:
        color = self.color_map.get(value, "gray")
        return render_to_string(request, self.template, {"formatter": self, "value": value, "color": color})


ProgressSize = typing.Literal["xxs", "xs", "sm", "md", "lg"]
ProgressColor = typing.Literal["accent", "gray", "red", "yellow", "green", "blue", "indigo", "purple", "pink"]


class ProgressFormatter(Formatter[int | float]):
    template: str = "ohmyadmin/formatters/progress.html"

    def __init__(
        self,
        *,
        size: ProgressSize = "sm",
        color: ProgressColor = "accent",
        label: str = "",
    ) -> None:
        self.size = size
        self.color = color
        self.label = label
