import datetime
import decimal
import typing

from starlette.datastructures import URL
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin.templating import render_to_string

TextAlign = typing.Literal["left", "right", "center"]
_T = typing.TypeVar("_T")


class FieldValueFormatter(typing.Protocol):  # pragma: no cover
    """
    Data formatter is a utility that renders object field value into a different way.

    For example, boolean can be rendered as icons or yes/no text.
    """

    def __call__(self, request: Request, value: typing.Any) -> str:
        ...


class BaseFormatter(typing.Generic[_T]):
    template: str = "ohmyadmin/formatters/value.html"

    def format(self, request: Request, value: _T) -> str:
        return render_to_string(request, self.template, {"formatter": self, "value": value})

    def __call__(self, request: Request, value: _T) -> str:
        return self.format(request, value)


class StringFormatter(BaseFormatter[str]):
    template: str = "ohmyadmin/formatters/string.html"

    def __init__(self, *, prefix: str = "", suffix: str = "") -> None:
        self.prefix = prefix
        self.suffix = suffix


class DateTimeFormatter(BaseFormatter[datetime.datetime]):
    template: str = "ohmyadmin/formatters/datetime.html"

    def __init__(self, format: typing.Literal["short", "medium", "long", "full"] = "medium") -> None:
        self.value_format = format


class DateFormatter(BaseFormatter[datetime.date | datetime.datetime]):
    template: str = "ohmyadmin/formatters/date.html"

    def __init__(self, format: typing.Literal["short", "medium", "long", "full"] = "medium") -> None:
        self.value_format = format


class TimeFormatter(BaseFormatter[datetime.datetime | datetime.time]):
    template: str = "ohmyadmin/formatters/time.html"

    def __init__(self, format: typing.Literal["short", "medium", "long", "full"] = "short") -> None:
        self.value_format = format


class BoolFormatter(BaseFormatter[bool]):
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


class AvatarFormatter(BaseFormatter[str]):
    template: str = "ohmyadmin/formatters/avatar.html"


LinkFactory: typing.TypeAlias = typing.Callable[[Request, typing.Any], URL]


class LinkFormatter(BaseFormatter[str]):
    template: str = "ohmyadmin/formatters/link.html"

    def __init__(
        self,
        *,
        url: str | URL | LinkFactory,
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


class NumberFormatter(BaseFormatter[int | float | decimal.Decimal]):
    template: str = "ohmyadmin/formatters/number.html"

    def __init__(self, *, prefix: str = "", suffix: str = "", align: TextAlign = "left", decimals: int = 2) -> None:
        self.prefix = prefix
        self.suffix = suffix
        self.align = align
        self.decimals = decimals

    def round_value(self, value: _T) -> _T:
        return round(value, self.decimals)


BadgeColor: typing.TypeAlias = typing.Literal["gray", "red", "yellow", "green", "blue", "indigo", "purple", "pink"]


class BadgeFormatter(BaseFormatter[str | int]):
    template: str = "ohmyadmin/formatters/badge.html"

    def __init__(self, *, color_map: dict[str | int, BadgeColor]) -> None:
        self.color_map = color_map or {}

    def format(self, request: Request, value: str | int) -> str:
        color = self.color_map.get(value, "gray")
        return render_to_string(request, self.template, {"formatter": self, "value": value, "color": color})


ProgressSize = typing.Literal["xxs", "xs", "sm", "md", "lg"]
ProgressColor = typing.Literal["accent", "gray", "red", "yellow", "green", "blue", "indigo", "purple", "pink"]


class ProgressFormatter(BaseFormatter[int | float]):
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


class CallbackFormatter(BaseFormatter[typing.Any]):
    def __init__(self, callback: typing.Callable[[Request, typing.Any], str]) -> None:
        self.callback = callback

    def format(self, request: Request, value: _T) -> str:
        return self.callback(request, value)
