import datetime
import decimal
import typing
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin.shortcuts import render_to_string

TextAlign = typing.Literal['left', 'right', 'center']
_T = typing.TypeVar('_T')


class DataFormatter(typing.Protocol):  # pragma: no cover
    """
    Data formatter is a utility that renders object field value into a different way.

    For example, boolean can be rendered as icons or yes/no text.
    """

    def __call__(self, request: Request, value: typing.Any) -> str:
        ...


class BaseFormatter(typing.Generic[_T]):
    template: str = 'ohmyadmin/formatters/string.html'

    def format(self, request: Request, value: _T) -> str:
        return render_to_string(request, self.template, {'formatter': self, 'value': value})

    def __call__(self, request: Request, value: _T) -> str:
        return self.format(request, value)


class StringFormatter(BaseFormatter[str]):
    pass


class DateTimeFormatter(BaseFormatter[datetime.datetime]):
    template: str = 'ohmyadmin/formatters/datetime.html'

    def __init__(self, format: typing.Literal['short', 'medium', 'long', 'full'] = 'medium') -> None:
        self.value_format = format


class DateFormatter(BaseFormatter[datetime.date | datetime.datetime]):
    template: str = 'ohmyadmin/formatters/date.html'

    def __init__(self, format: typing.Literal['short', 'medium', 'long', 'full'] = 'medium') -> None:
        self.value_format = format


class TimeFormatter(BaseFormatter[datetime.datetime | datetime.time]):
    template: str = 'ohmyadmin/formatters/time.html'

    def __init__(self, format: typing.Literal['short', 'medium', 'long', 'full'] = 'short') -> None:
        self.value_format = format


class BoolFormatter(BaseFormatter[bool]):
    template: str = 'ohmyadmin/formatters/bool.html'

    def __init__(
        self,
        as_text: bool = False,
        true_text: str = _('Yes', domain='ohmyadmin'),
        false_text: str = _('No', domain='ohmyadmin'),
    ) -> None:
        self.true_text = true_text
        self.false_text = false_text
        self.as_text = as_text


class AvatarFormatter(BaseFormatter[str]):
    template: str = 'ohmyadmin/formatters/avatar.html'


class NumberFormatter(BaseFormatter[int | float | decimal.Decimal]):
    template: str = 'ohmyadmin/formatters/number.html'

    def __init__(self, *, prefix: str = '', suffix: str = '', align: TextAlign = 'right') -> None:
        self.prefix = prefix
        self.suffix = suffix
        self.align = align


BadgeColor: typing.TypeAlias = typing.Literal['gray', 'red', 'yellow', 'green', 'blue', 'indigo', 'purple', 'pink']


class BadgeFormatter(BaseFormatter[str | int]):
    template: str = 'ohmyadmin/formatters/badge.html'

    def __init__(self, *, color_map: dict[str | int, BadgeColor]) -> None:
        self.color_map = color_map or {}

    def format(self, request: Request, value: str | int) -> str:
        color = self.color_map.get(value, 'gray')
        return render_to_string(request, self.template, {'formatter': self, 'value': value, 'color': color})


ProgressSize = typing.Literal['xxs', 'xs', 'sm', 'md', 'lg']
ProgressColor = typing.Literal['accent', 'gray', 'red', 'yellow', 'green', 'blue', 'indigo', 'purple', 'pink']


class ProgressFormatter(BaseFormatter[int | float]):
    template: str = 'ohmyadmin/formatters/progress.html'

    def __init__(
        self,
        *,
        size: ProgressSize = 'sm',
        color: ProgressColor = 'accent',
        label: str = '',
    ) -> None:
        self.size = size
        self.color = color
        self.label = label
