from __future__ import annotations

import dataclasses

import abc
import decimal
import inspect
import logging
import typing
import wtforms
from markupsafe import Markup
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

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
        await self.initialize(request)

    async def initialize(self, request: Request) -> None:
        pass

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
        try:
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
        except Exception as ex:
            logging.exception(ex)
            return Markup(f'Error: {ex}')


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
    query = wtforms.StringField(validators=[wtforms.validators.data_required()])


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
    query = wtforms.IntegerField(validators=[wtforms.validators.data_required()])


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
    query = wtforms.FloatField(validators=[wtforms.validators.data_required()])


class FloatFilter(IntegerFilter):
    form_class = FloatFilterForm


class DecimalFilterForm(wtforms.Form):
    operation = wtforms.SelectField(choices=NumberOperation.choices())
    query = wtforms.DecimalField(validators=[wtforms.validators.data_required()])


class DecimalFilter(IntegerFilter):
    form_class = DecimalFilterForm


class DateFilterForm(wtforms.Form):
    query = wtforms.DateField()


class DateFilter(BaseFilter[DateFilterForm]):
    form_class = DateFilterForm
    indicator_template = 'ohmyadmin/filters/date_indicator.html'

    def apply(self, request: Request, query: DataSource) -> DataSource:
        value = self.form.data['query']
        if not value:
            return query
        return query.apply_date_filter(self.query_param, value)

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data['query'])

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return {
            'value': value['query'],
        }


class DateRangeFilterForm(wtforms.Form):
    after = wtforms.DateField()
    before = wtforms.DateField()


class DateRangeFilter(BaseFilter[DateRangeFilterForm]):
    form_class = DateRangeFilterForm
    indicator_template = 'ohmyadmin/filters/date_range_indicator.html'

    def apply(self, request: Request, query: DataSource) -> DataSource:
        before = self.form.data['before']
        after = self.form.data['after']
        return query.apply_date_range_filter(self.query_param, before, after)

    def is_active(self, request: Request) -> bool:
        return self.form.data['before'] or self.form.data['after']

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return {
            'before': value['before'],
            'after': value['after'],
        }


class ChoiceFilterForm(wtforms.Form):
    choice = wtforms.SelectField(
        label=_('Choices', domain='ohmyadmin'), validators=[wtforms.validators.data_required()]
    )


class ChoiceFilter(BaseFilter[ChoiceFilterForm]):
    form_class = ChoiceFilterForm
    indicator_template = 'ohmyadmin/filters/choice_indicator.html'

    def __init__(
        self,
        query_param: str,
        label: str = '',
        *,
        choices: typing.Any,
        coerce: type[str | int | float | decimal.Decimal] = str,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(query_param, label, **kwargs)
        self.coerce = coerce
        self.choices = choices
        self.form.choice.coerce = self.coerce

    async def initialize(self, request: Request) -> None:
        if inspect.iscoroutinefunction(self.choices):
            self.form.choice.choices = await self.choices()
        elif callable(self.choices):
            self.form.choice.choices = self.choices()
        else:
            self.form.choice.choices = self.choices

    def apply(self, request: Request, query: DataSource) -> DataSource:
        choice = self.form.data['choice']
        if not choice:
            return query
        return query.apply_choice_filter(self.query_param, [choice], self.coerce)

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data['choice'])

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        choice = next((choice for choice in self.form.choice.choices if choice[0] == value['choice']))
        return {'value': choice[1]}


class MultiChoiceFilterForm(wtforms.Form):
    choice = wtforms.SelectMultipleField(
        label=_('Select multiple', domain='ohmyadmin'), validators=[wtforms.validators.data_required()]
    )


class MultiChoiceFilter(BaseFilter[MultiChoiceFilterForm]):
    form_class = MultiChoiceFilterForm
    indicator_template = 'ohmyadmin/filters/multi_choice_indicator.html'

    def __init__(
        self,
        query_param: str,
        label: str = '',
        *,
        choices: typing.Any,
        coerce: type[str | int | float | decimal.Decimal] = str,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(query_param, label, **kwargs)
        self.coerce = coerce
        self.choices = choices
        self.form.choice.coerce = self.coerce

    async def initialize(self, request: Request) -> None:
        if inspect.iscoroutinefunction(self.choices):
            self.form.choice.choices = await self.choices()
        elif callable(self.choices):
            self.form.choice.choices = self.choices()
        else:
            self.form.choice.choices = self.choices

    def apply(self, request: Request, query: DataSource) -> DataSource:
        choice = self.form.data['choice']
        if not choice:
            return query
        return query.apply_choice_filter(self.query_param, choice, self.coerce)

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data['choice'])

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        choices = (choice for choice in self.form.choice.choices if choice[0] in value['choice'])
        values = [choice[1] for choice in choices]
        return {'value': values}
