from __future__ import annotations

import abc
import datetime
import decimal
import inspect
import typing
import wtforms
from markupsafe import Markup
from starlette.requests import Request
from wtforms.fields.core import UnboundField
from wtforms.meta import DefaultMeta

from ohmyadmin import display
from ohmyadmin.forms import (
    CheckboxListWidget,
    Choices,
    ChoicesFactory,
    DecimalField,
    FloatField,
    Form,
    IntegerField,
    Prefill,
    SelectField,
)
from ohmyadmin.helpers import snake_to_sentence
from ohmyadmin.i18n import _
from ohmyadmin.templating import macro


class BaseFilter(abc.ABC):
    label: str = ''
    form_field_class: typing.Type[wtforms.Field] = wtforms.StringField

    def __init__(self, query_param: str, label: str = '') -> None:
        self.coerce: typing.Callable = str
        self.query_param = query_param
        self.label = label or snake_to_sentence(self.query_param)
        self.unbound_field: UnboundField = self.form_field_class()

    def create_form_field(self, request: Request) -> wtforms.Field:
        field = self.unbound_field.bind(form=None, name=self.query_param, _meta=DefaultMeta())
        field.process(request.query_params)
        return field

    def is_active(self, request: Request) -> bool:
        field = self.create_form_field(request)
        if not field.validate(wtforms.Form()):
            return False
        return bool(field.data)

    def get_value(self, request: Request) -> typing.Any | None:
        field = self.create_form_field(request)
        if not field.validate(wtforms.Form()):
            raise wtforms.ValidationError(''.join(field.errors))
        return field.data

    @abc.abstractmethod
    def apply(self, request: Request, stmt: typing.Any, value: typing.Any) -> typing.Any:
        ...

    def filter(self, request: Request, stmt: typing.Any) -> typing.Any:
        try:
            if value := self.get_value(request):
                return self.apply(request, stmt, value)
        except wtforms.ValidationError:
            pass
        return stmt

    @abc.abstractmethod
    def render_indicator(self, request: Request) -> str:
        ...

    @abc.abstractmethod
    def render_form_field(self, request: Request) -> str:
        ...


class BaseDateFilter(BaseFilter):
    form_field_class = wtforms.DateField

    def render_indicator(self, request: Request) -> str:
        value = self.get_value(request)
        component = display.DateTime()
        display_value = component.render(value.isoformat()) if value else 'n/a'
        macros = macro('ohmyadmin/filters.html', 'filter_indicator')
        url = request.url.remove_query_params(self.query_param)
        return macros(url, self.label, display_value)

    def render_form_field(self, request: Request) -> str:
        field = self.create_form_field(request)
        macros = macro('ohmyadmin/filters.html', 'filter_field')
        return macros(field)


class DateRangeFilterForm(wtforms.Form):
    before = wtforms.DateField(validators=[wtforms.validators.optional()])
    after = wtforms.DateField(validators=[wtforms.validators.optional()])


class BaseDateRangeFilter(BaseFilter):
    def __init__(self, query_param: str, label: str = '') -> None:
        super().__init__(query_param, label)
        self.unbound_field = wtforms.FormField(DateRangeFilterForm, label=label)

    def apply(self, request: Request, stmt: typing.Any, value: typing.Any) -> typing.Any:
        try:
            value = self.get_value(request)
            value_before = value['before']
            value_after = value['after']
            return self.apply_filter(request, stmt, value_before, value_after)
        except wtforms.ValidationError:
            pass
        return stmt

    @abc.abstractmethod
    def apply_filter(
        self,
        request: Request,
        stmt: typing.Any,
        before: datetime.date | None,
        after: datetime.date | None,
    ) -> typing.Any:
        ...

    def is_active(self, request: Request) -> bool:
        field = self.create_form_field(request)
        return bool(field.data['before'] or field.data['after'])

    def render_indicator(self, request: Request) -> str:
        try:
            value: dict | None = self.get_value(request)
            if not value:
                return ''
        except wtforms.ValidationError:
            return ''

        value_before = value.get('before')
        value_after = value.get('after')
        value_html = ''
        if value_before and value_after:
            formatted_before = display.DateTime().render(value_before.isoformat())
            formatted_after = display.DateTime().render(value_after.isoformat())
            value_html = _(
                'between <span class="text-amber-700 font-medium">{before}</span> '
                'and <span class="text-amber-700 font-medium">{after}</span>'
            ).format(before=formatted_before, after=formatted_after)
        elif value_before:
            value_html = _('before <span class="text-amber-700 font-medium">{date}</span>').format(
                date=display.DateTime().render(value_before.isoformat()),
            )
        elif value_after:
            value_html = _('after <span class="text-amber-700 font-medium">{date}</span>').format(
                date=display.DateTime().render(value_after.isoformat()),
            )

        field = self.create_form_field(request)
        macros = macro('ohmyadmin/filters.html', 'filter_indicator')
        url = request.url.remove_query_params([field.before.name, field.after.name])
        return macros(url, self.label, value_html)

    def render_form_field(self, request: Request) -> str:
        field = self.create_form_field(request)
        macros = macro('ohmyadmin/filters.html', 'list_filter_field')
        return macros(field)


class BaseChoiceFilter(BaseFilter, Prefill):
    def __init__(
        self, choices: Choices | ChoicesFactory, query_param: str, coerce: typing.Callable = str, label: str = ''
    ) -> None:
        super().__init__(query_param, label)
        self.unbound_field = wtforms.SelectField(coerce=coerce)
        self.choices: Choices = []
        self.choices_factory: ChoicesFactory | None = None
        if choices:
            if callable(choices) and inspect.iscoroutinefunction(choices):
                self.choices_factory = choices
            else:
                self.choices = choices  # type: ignore

    async def prefill(self, request: Request, form: Form) -> None:
        if self.choices_factory:
            self.choices = await self.choices_factory(request, wtforms.Form())

    def create_form_field(self, request: Request) -> wtforms.Field:
        field = self.unbound_field.bind(form=None, name=self.query_param, _meta=DefaultMeta())
        field.process(request.query_params)
        field.choices = self.choices
        return field

    def render_indicator(self, request: Request) -> str:
        value = self.get_value(request)

        for (choice_value, choice_label) in self.choices:
            if choice_value == value:
                value = choice_label
                break

        component = display.Text()
        display_value = component.render(value) if value else 'n/a'
        macros = macro('ohmyadmin/filters.html', 'filter_indicator')
        url = request.url.remove_query_params(self.query_param)
        return macros(url, self.label, display_value)

    def render_form_field(self, request: Request) -> str:
        field = self.create_form_field(request)
        macros = macro('ohmyadmin/filters.html', 'filter_field')
        return macros(field)


_VT = typing.TypeVar('_VT')


class BaseNumericFilter(BaseFilter, typing.Generic[_VT]):
    operations = (
        ('eq', _('equals')),
        ('gt', _('is greater than')),
        ('gte', _('is greater than or equal')),
        ('lt', _('is less than')),
        ('lte', _('is less than or equal')),
    )

    def __init__(self, query_param: str, label: str = '') -> None:
        super().__init__(query_param, label)
        self.operations_by_key: dict[str, str] = {x[0]: x[1] for x in self.operations}
        self.unbound_field = wtforms.FormField(self.get_subform_class(), label=label)

    def apply(self, request: Request, stmt: typing.Any, value: typing.Any) -> typing.Any:
        operation = value['operation']
        query = value['query']
        if not query:
            return stmt
        return self.apply_operation(request, stmt, operation, query)

    @abc.abstractmethod
    def apply_operation(
        self,
        request: Request,
        stmt: typing.Any,
        operation: typing.Literal['eq', 'gt', 'gte', 'lt', 'lte'],
        query: _VT,
    ) -> typing.Any:
        ...

    @abc.abstractmethod
    def get_subform_class(self) -> typing.Type[wtforms.Form]:
        ...

    def is_active(self, request: Request) -> bool:
        field = self.create_form_field(request)
        return bool(field.data['query'])

    def render_indicator(self, request: Request) -> str:
        try:
            value: dict | None = self.get_value(request)
            if not value:
                return ''
        except wtforms.ValidationError:
            return ''

        value_html = Markup(
            '<span class="font-medium text-amber-700">{operation}</span> {value}'.format(
                operation=self.operations_by_key[value['operation']].lower(),
                value=value['query'],
            )
        )
        field = self.create_form_field(request)
        component = display.Text()
        display_value = component.render(value_html) if value else 'n/a'
        macros = macro('ohmyadmin/filters.html', 'filter_indicator')
        url = request.url.remove_query_params([field.operation.name, field.query.name])
        return macros(url, self.label, display_value)

    def render_form_field(self, request: Request) -> str:
        field = self.create_form_field(request)
        macros = macro('ohmyadmin/filters.html', 'list_filter_field')
        return macros(field)


class BaseIntegerFilter(BaseNumericFilter[int]):
    def get_subform_class(self) -> typing.Type[wtforms.Form]:
        class SubForm(wtforms.Form):
            operation = SelectField(choices=self.operations)
            query = IntegerField()

        return SubForm


class BaseFloatFilter(BaseNumericFilter[float]):
    def get_subform_class(self) -> typing.Type[wtforms.Form]:
        class SubForm(wtforms.Form):
            operation = SelectField(choices=self.operations)
            query = FloatField()

        return SubForm


class BaseDecimalFilter(BaseNumericFilter[decimal.Decimal]):
    def get_subform_class(self) -> typing.Type[wtforms.Form]:
        class SubForm(wtforms.Form):
            operation = SelectField(choices=self.operations)
            query = DecimalField()

        return SubForm


class BaseStringFilter(BaseFilter):
    operations = (
        ('exact', _('same as')),
        ('startswith', _('starts with')),
        ('endswith', _('ends with')),
        ('contains', _('contains')),
        ('pattern', _('matches')),
    )

    def __init__(self, query_param: str, label: str = '') -> None:
        super().__init__(query_param, label)
        self.operations_by_key: dict[str, str] = {x[0]: x[1] for x in self.operations}
        self.unbound_field = wtforms.FormField(self.get_subform_class(), label=label)

    def apply(self, request: Request, stmt: typing.Any, value: typing.Any) -> typing.Any:
        operation = value['operation']
        query = value['query']
        if not query:
            return stmt
        return self.apply_operation(request, stmt, operation, query)

    @abc.abstractmethod
    def apply_operation(
        self,
        request: Request,
        stmt: typing.Any,
        operation: typing.Literal['exact', 'startswith', 'endswith', 'contains', 'pattern'],
        query: str,
    ) -> typing.Any:
        ...

    def get_subform_class(self) -> typing.Type[wtforms.Form]:
        class SubForm(wtforms.Form):
            operation = wtforms.SelectField(choices=self.operations)
            query = wtforms.StringField(validators=[wtforms.validators.data_required()])

        return SubForm

    def is_active(self, request: Request) -> bool:
        field = self.create_form_field(request)
        return bool(field.data['query'])

    def render_indicator(self, request: Request) -> str:
        try:
            value: dict | None = self.get_value(request)
            if not value:
                return ''
        except wtforms.ValidationError:
            return ''

        value_html = Markup(
            '<span class="font-medium text-amber-700">{operation}</span> {value}'.format(
                operation=self.operations_by_key[value['operation']].lower(),
                value=value['query'],
            )
        )
        field = self.create_form_field(request)
        component = display.Text()
        display_value = component.render(value_html) if value else 'n/a'
        macros = macro('ohmyadmin/filters.html', 'filter_indicator')
        url = request.url.remove_query_params([field.operation.name, field.query.name])
        return macros(url, self.label, display_value)

    def render_form_field(self, request: Request) -> str:
        field = self.create_form_field(request)
        macros = macro('ohmyadmin/filters.html', 'list_filter_field')
        return macros(field)


class BaseMultiChoiceFilter(BaseChoiceFilter):
    def __init__(
        self, choices: Choices | ChoicesFactory, query_param: str, coerce: typing.Callable = str, label: str = ''
    ) -> None:
        super().__init__(choices, query_param, coerce, label)
        self.unbound_field = wtforms.SelectMultipleField(
            option_widget=wtforms.widgets.CheckboxInput(),
            widget=CheckboxListWidget(),
            coerce=coerce,
        )

    def render_indicator(self, request: Request) -> str:
        try:
            value: list | None = self.get_value(request)
            if not value:
                return ''
        except wtforms.ValidationError:
            return ''

        field = self.create_form_field(request)
        choices_by_key = {x[0]: x[1] for x in field.choices}
        labels = [choices_by_key[label] for label in value]
        component = display.Text()
        display_value = component.render(', '.join(labels)) if value else 'n/a'
        macros = macro('ohmyadmin/filters.html', 'filter_indicator')
        url = request.url.remove_query_params(self.query_param)
        return macros(url, self.label, display_value)
