from __future__ import annotations

import dataclasses

import abc
import typing
import wtforms
from starlette.requests import Request

from ohmyadmin.datasource.base import DataSource, NumberOperation, StringOperation
from ohmyadmin.helpers import snake_to_sentence
from ohmyadmin.shortcuts import render_to_string

_FT = typing.TypeVar('_FT', bound=wtforms.Form)


class BaseFilter(abc.ABC, typing.Generic[_FT]):
    template: str = 'ohmyadmin/filters/form.html'
    indicator_template: str = 'ohmyadmin/filters/blank_indicator.html'
    form_class: type[_FT] = wtforms.Form
    form: _FT

    def __new__(cls, *args: typing.Any, **kwargs: typing.Any) -> UnboundFilter | BaseFilter:  # type: ignore[misc]
        if '_create' in kwargs:
            return super().__new__(cls)
        return UnboundFilter(cls, args, kwargs)

    def __init__(self, query_param: str, label: str = '', **kwargs: typing.Any) -> None:
        self.query_param = query_param
        self.label = label or snake_to_sentence(self.query_param.title())
        self.form = self.form_class(prefix=self.query_param)

    async def prepare(self, request: Request) -> None:
        self.form.process(request.query_params)

    @abc.abstractmethod
    def apply(self, request: Request, query: DataSource) -> DataSource:
        ...

    @abc.abstractmethod
    def is_active(self, request: Request) -> bool:
        ...

    @abc.abstractmethod
    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        ...

    def render_form(self, request: Request) -> str:
        return render_to_string(request, self.template, {'filter': self, 'form': self.form})

    def render_indicator(self, request: Request) -> str:
        clear_url = request.url.remove_query_params([form_field.name for form_field in self.form]).include_query_params(
            clear=1
        )
        indicator = self.get_indicator_context(self.form.data)
        return render_to_string(
            request,
            self.indicator_template,
            {
                'filter': self,
                'indicator': indicator,
                'clear_url': clear_url,
            },
        )


@dataclasses.dataclass
class UnboundFilter:
    filter_class: type[BaseFilter]
    args: tuple[typing.Any, ...]
    kwargs: dict[str, typing.Any]

    async def create(self, request: Request) -> BaseFilter:
        instance = self.filter_class(*self.args, _create=True, **self.kwargs)
        await instance.prepare(request)
        return instance


class StringFilterForm(wtforms.Form):
    operation = wtforms.SelectField(choices=StringOperation.choices())
    query = wtforms.StringField()


class StringFilter(BaseFilter[StringFilterForm]):
    form_class = StringFilterForm
    indicator_template = 'ohmyadmin/filters/enum_indicator.html'

    def apply(self, request: Request, query: DataSource) -> DataSource:
        operation = self.form.data['operation']
        if not operation:
            return query

        value = self.form.data['query']
        return query.apply_string_filter(self.query_param, StringOperation[operation], value)

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data['query'])

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return {
            'operation': StringOperation[value['operation']],
            'value': value['query'],
        }


class IntegerFilterForm(wtforms.Form):
    operation = wtforms.SelectField(choices=NumberOperation.choices())
    query = wtforms.IntegerField()


class IntegerFilter(BaseFilter[IntegerFilterForm]):
    form_class = IntegerFilterForm
    indicator_template = 'ohmyadmin/filters/enum_indicator.html'

    def apply(self, request: Request, query: DataSource) -> DataSource:
        operation = self.form.data['operation']
        if not operation:
            return query
        operation = NumberOperation[operation]
        value = self.form.data['query']
        return query.apply_number_filter(self.query_param, operation, value)

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data['query'])

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return {
            'operation': NumberOperation[value['operation']],
            'value': value['query'],
        }


class FloatFilterForm(wtforms.Form):
    operation = wtforms.SelectField(choices=NumberOperation.choices())
    query = wtforms.IntegerField()


class FloatFilter(IntegerFilter):
    form_class = FloatFilterForm


class DecimalFilterForm(wtforms.Form):
    operation = wtforms.SelectField(choices=NumberOperation.choices())
    query = wtforms.IntegerField()


class DecimalFilter(IntegerFilter):
    form_class = DecimalFilterForm
