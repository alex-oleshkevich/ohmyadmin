from __future__ import annotations

import dataclasses

import abc
import decimal
import functools
import inspect
import typing
import wtforms
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin.datasource.base import DataSource, NumberOperation, StringOperation
from ohmyadmin.forms import AsyncSelectField, AsyncSelectMultipleField, init_form
from ohmyadmin.helpers import snake_to_sentence
from ohmyadmin.shortcuts import render_to_string

_FT = typing.TypeVar('_FT', bound=wtforms.Form)
_T = typing.TypeVar('_T', bound='BaseFilter')


class BaseFilter(abc.ABC, typing.Generic[_FT]):
    """Base filter class for data filters."""

    template: str = 'ohmyadmin/filters/form.html'
    indicator_template: str = 'ohmyadmin/filters/blank_indicator.html'
    form_class: type[_FT] = wtforms.Form
    form: _FT

    def __new__(  # type: ignore[misc]
        cls,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> UnboundFilter[_T] | BaseFilter[_FT]:
        """
        We attach filters as instances to let users customize it via constructor arguments.

        However, this creates mutable singletons. To workaround, we create unbound filters which are like factories and
        create actual instances when called. There may be a better idea but the current one is good enough for this
        purpose.
        """
        if '_create' in kwargs:
            return super().__new__(cls)

        return UnboundFilter(cls, args, kwargs)  # type: ignore[arg-type]

    def __init__(self, query_param: str, label: str = '', **kwargs: typing.Any) -> None:
        self.query_param = query_param
        self.label = label or snake_to_sentence(self.query_param.title())
        self.form = self.form_class(prefix=self.query_param)

    async def prepare(self, request: Request) -> None:
        """
        Creation hook to execute async operations when page creates the filter.

        As a user you have to override `BaseFilter.initialize` instead of this method.
        """
        self.form.process(request.query_params)
        await self.initialize(request)

    async def initialize(self, request: Request) -> None:
        """Override this method if you want to call async code when page instantiates the filter."""

    @abc.abstractmethod
    def apply(self, request: Request, query: DataSource) -> DataSource:
        """Apply filter to the data source query."""

    @abc.abstractmethod
    def is_active(self, request: Request) -> bool:
        """
        Check if the filter is active.

        Active filters rendered differently in the filter bar.
        """

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """
        Various filters render different data in the indicators. This method returns template context for indicators.
        The context available in the indicator template via `indicator` template variable.

        :param value: current form data.
        """
        return value

    def render_form(self, request: Request) -> str:
        return render_to_string(request, self.template, {'filter': self, 'form': self.form})

    def render_indicator(self, request: Request) -> str:
        """
        Render indicator.

        Indicators visible only when filter is active.
        """
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
class UnboundFilter(typing.Generic[_T]):
    """A filter factory."""

    filter_class: type[_T]
    args: tuple[typing.Any, ...]
    kwargs: dict[str, typing.Any]

    async def create(self, request: Request) -> _T:
        """Create a filter instance."""
        instance = self.filter_class(*self.args, _create=True, **self.kwargs)
        await instance.prepare(request)
        return instance


def _safe_enum_coerce(value: typing.Any, choices: type[StringOperation | NumberOperation]) -> typing.Any:
    try:
        return choices[value]
    except KeyError:
        return None


class StringFilterForm(wtforms.Form):
    operation = wtforms.SelectField(
        choices=StringOperation.choices(),
        coerce=functools.partial(_safe_enum_coerce, choices=StringOperation),
    )
    query = wtforms.StringField(validators=[wtforms.validators.data_required()])


class StringFilter(BaseFilter[StringFilterForm]):
    """
    String filters let users query data that matches text and rule.

    Rules defined by StringOperation and are like `starts with`, `ends with`, etc.
    """

    form_class = StringFilterForm
    indicator_template = 'ohmyadmin/filters/enum_indicator.html'

    def apply(self, request: Request, query: DataSource) -> DataSource:
        operation = self.form.data['operation']
        if not operation:
            return query

        value = self.form.data['query']
        return query.apply_string_filter(self.query_param, operation, value)

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data['query'])


class IntegerFilterForm(wtforms.Form):
    operation = wtforms.SelectField(
        choices=NumberOperation.choices(),
        coerce=functools.partial(_safe_enum_coerce, choices=NumberOperation),
    )
    query = wtforms.IntegerField(validators=[wtforms.validators.data_required()])


class IntegerFilter(BaseFilter[IntegerFilterForm]):
    form_class = IntegerFilterForm
    indicator_template = 'ohmyadmin/filters/enum_indicator.html'

    def apply(self, request: Request, query: DataSource) -> DataSource:
        operation = self.form.data['operation']
        if not operation:
            return query

        value = self.form.data['query']
        return query.apply_number_filter(self.query_param, operation, value)

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data['query'])


class FloatFilterForm(wtforms.Form):
    operation = wtforms.SelectField(
        choices=NumberOperation.choices(),
        coerce=functools.partial(_safe_enum_coerce, choices=NumberOperation),
    )
    query = wtforms.FloatField(validators=[wtforms.validators.data_required()])


class FloatFilter(IntegerFilter):
    form_class = FloatFilterForm


class DecimalFilterForm(wtforms.Form):
    operation = wtforms.SelectField(
        choices=NumberOperation.choices(),
        coerce=functools.partial(_safe_enum_coerce, choices=NumberOperation),
    )
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


class DateRangeFilterForm(wtforms.Form):
    after = wtforms.DateField()
    before = wtforms.DateField()


class DateRangeFilter(BaseFilter[DateRangeFilterForm]):
    form_class = DateRangeFilterForm
    indicator_template = 'ohmyadmin/filters/date_range_indicator.html'

    def apply(self, request: Request, query: DataSource) -> DataSource:
        before = self.form.data['before']
        after = self.form.data['after']
        if before or after:
            return query.apply_date_range_filter(self.query_param, before, after)
        return query

    def is_active(self, request: Request) -> bool:
        return self.form.data['before'] or self.form.data['after']

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        value['format'] = 'date'
        return super().get_indicator_context(value)


class DateTimeRangeFilterForm(wtforms.Form):
    after = wtforms.DateTimeLocalField()
    before = wtforms.DateTimeLocalField()


class DateTimeRangeFilter(BaseFilter[DateRangeFilterForm]):
    form_class = DateTimeRangeFilterForm
    indicator_template = 'ohmyadmin/filters/date_range_indicator.html'

    def apply(self, request: Request, query: DataSource) -> DataSource:
        before = self.form.data['before']
        after = self.form.data['after']
        if self.is_active(request):
            return query.apply_date_range_filter(self.query_param, before, after)
        return query

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data['before'] or self.form.data['after'])

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        value['format'] = 'datetime'
        return super().get_indicator_context(value)


class ChoiceFilterForm(wtforms.Form):
    choice = AsyncSelectField(
        label=_('Choices', domain='ohmyadmin'),
        validators=[wtforms.validators.data_required()],
        choices=[],
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
        self.form.choice.coerce = self.coerce
        if inspect.iscoroutinefunction(choices):
            self.form.choice.choices_loader = choices
        else:
            self.form.choice.choices = choices

    async def initialize(self, request: Request) -> None:
        await init_form(request, self.form)

    def apply(self, request: Request, query: DataSource) -> DataSource:
        if self.is_active(request):
            choice = self.form.data['choice']
            return query.apply_choice_filter(self.query_param, [choice], self.coerce)
        return query

    def is_active(self, request: Request) -> bool:
        if self.form.validate():
            return bool(self.form.data['choice'])
        return False

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        by_key = {choice[0]: choice[1] for choice in self.form.choice.choices}
        choice = by_key.get(value['choice'], '')
        return {'value': choice}


class MultiChoiceFilterForm(wtforms.Form):
    choice = AsyncSelectMultipleField(
        label=_('Select multiple', domain='ohmyadmin'),
        validators=[wtforms.validators.data_required()],
        choices=[],
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
        if inspect.iscoroutinefunction(choices):
            self.form.choice.choices_loader = choices
        else:
            self.form.choice.choices = choices
        self.form.choice.coerce = self.coerce

    async def initialize(self, request: Request) -> None:
        await init_form(request, self.form)

    def apply(self, request: Request, query: DataSource) -> DataSource:
        if self.is_active(request):
            choice = self.form.data['choice']
            return query.apply_choice_filter(self.query_param, choice, self.coerce)
        return query

    def is_active(self, request: Request) -> bool:
        if self.form.validate():
            return bool(self.form.data['choice'])
        return False

    def get_indicator_context(self, value: dict[str, typing.Any]) -> dict[str, typing.Any]:
        choices = (choice for choice in self.form.choice.choices if choice[0] in value['choice'])
        values = [choice[1] for choice in choices]
        return {'value': values}
