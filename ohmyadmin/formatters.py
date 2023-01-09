import datetime
import typing

from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin.shortcuts import render_to_string


class DataFormatter(typing.Protocol):
    def __call__(self, request: Request, value: typing.Any) -> str: ...


class BaseFormatter:
    template: str = 'ohmyadmin/formatters/string.html'

    def format(self, request: Request, value: datetime.date) -> str:
        return render_to_string(request, self.template, {'formatter': self, 'value': value})

    def __call__(self, request: Request, value: typing.Any) -> str:
        return self.format(request, value)


class ToStringFormatter(BaseFormatter):
    pass


class DateTimeFormatter(BaseFormatter):
    template: str = 'ohmyadmin/formatters/datetime.html'

    def __init__(self, format: typing.Literal['short', 'medium', 'long', 'full'] = 'medium') -> None:
        self.value_format = format


class DateFormatter(BaseFormatter):
    template: str = 'ohmyadmin/formatters/date.html'

    def __init__(self, format: typing.Literal['short', 'medium', 'long', 'full'] = 'medium') -> None:
        self.value_format = format


class TimeFormatter(BaseFormatter):
    template: str = 'ohmyadmin/formatters/time.html'

    def __init__(self, format: typing.Literal['short', 'medium', 'long', 'full'] = 'medium') -> None:
        self.value_format = format


class BoolFormatter(BaseFormatter):
    template: str = 'ohmyadmin/formatters/bool.html'

    def __init__(
        self, as_text: bool = False,
        true_text: str = _('Yes', domain='ohmyadmin'),
        false_text: str = _('No', domain='ohmyadmin'),
    ) -> None:
        self.true_text = true_text
        self.false_text = false_text
        self.as_text = as_text


class AvatarFormatter(BaseFormatter):
    template: str = 'ohmyadmin/formatters/avatar.html'
