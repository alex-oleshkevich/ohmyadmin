from __future__ import annotations

import abc
import datetime
import typing
import wtforms
from starlette.requests import Request
from wtforms.fields.core import UnboundField
from wtforms.meta import DefaultMeta

from ohmyadmin.components import display
from ohmyadmin.helpers import snake_to_sentence
from ohmyadmin.templating import macro


class BaseFilter(abc.ABC):
    label: str = ''
    value_converter: typing.Callable = str

    def __init__(self, query_param: str, label: str = '') -> None:
        self.query_param = query_param
        self.label = label or snake_to_sentence(self.query_param)

    @abc.abstractmethod
    def apply(self, request: Request, stmt: typing.Any, value: typing.Any) -> typing.Any:
        ...

    def filter(self, request: Request, stmt: typing.Any) -> typing.Any:
        value = self.get_value(request)
        if value is not None:
            return self.apply(request, stmt, value)
        return stmt

    def is_active(self, request: Request) -> bool:
        return self.get_value(request) is not None

    def get_value(self, request: Request) -> typing.Any | None:
        raw_value = request.query_params.get(self.query_param)
        if raw_value:
            try:
                return self.convert_value(raw_value)
            except ValueError:
                pass
        return None

    def convert_value(self, value: str) -> typing.Any:
        return self.value_converter(value)

    @abc.abstractmethod
    def render_indicator(self, request: Request) -> str:
        ...

    @abc.abstractmethod
    def render_form_field(self, request: Request) -> str:
        ...


class BaseDateFilter(BaseFilter):
    value_converter = datetime.date.fromisoformat

    def render_indicator(self, request: Request) -> str:
        value = self.get_value(request)
        component = display.DateTime()
        display_value = component.render(value.isoformat()) if value else 'n/a'
        macros = macro('ohmyadmin/filters.html', 'filter_indicator')
        url = request.url.remove_query_params(self.query_param)
        return macros(url, self.label, display_value)

    def render_form_field(self, request: Request) -> str:
        unbound_field: UnboundField = wtforms.DateField(label=self.label)
        field = unbound_field.bind(form=None, name=self.query_param, _meta=DefaultMeta())
        field.process(formdata=None, data=self.get_value(request))
        macros = macro('ohmyadmin/filters.html', 'date_filter')
        return macros(field)
