from __future__ import annotations

import abc
import datetime
import inspect
import typing
import wtforms
from markupsafe import Markup
from starlette.requests import Request
from wtforms.fields.core import UnboundField
from wtforms.meta import DefaultMeta

from ohmyadmin.components import display
from ohmyadmin.forms import Choices, ChoicesFactory, Form, Prefill
from ohmyadmin.helpers import snake_to_sentence
from ohmyadmin.i18n import _
from ohmyadmin.templating import macro


class BaseFilter(abc.ABC):
    label: str = ''

    def __init__(self, query_param: str, label: str = '') -> None:
        self.coerce: typing.Callable = str
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
        return self.coerce(value)

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
        macros = macro('ohmyadmin/filters.html', 'filter_field')
        return macros(field)


class BaseSelectFilter(BaseFilter, Prefill):
    def __init__(
        self, choices: Choices | ChoicesFactory, query_param: str, coerce: typing.Callable = str, label: str = ''
    ) -> None:
        super().__init__(query_param, label)

        self.coerce = coerce
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
        unbound_field: UnboundField = wtforms.SelectField(label=self.label, choices=self.choices, coerce=self.coerce)
        field = unbound_field.bind(form=None, name=self.query_param, _meta=DefaultMeta())
        field.process(formdata=None, data=self.get_value(request))
        macros = macro('ohmyadmin/filters.html', 'filter_field')
        return macros(field)


class BaseNumberFilter(BaseFilter):
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

        class SubForm(wtforms.Form):
            operation = wtforms.SelectField(choices=self.operations)
            query = wtforms.IntegerField()

        self.unbound_field = wtforms.FormField(SubForm, label=label)

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
        query: int,
    ) -> typing.Any:
        ...

    def create_form_field(self, request: Request) -> wtforms.Field:
        field = self.unbound_field.bind(form=None, name=self.query_param, _meta=DefaultMeta())
        field.process(request.query_params)
        return field

    def is_active(self, request: Request) -> bool:
        field = self.create_form_field(request)
        return bool(field.data['query'])

    def get_value(self, request: Request) -> typing.Any | None:
        return self.create_form_field(request).data

    def render_indicator(self, request: Request) -> str:
        value = self.get_value(request)
        assert value

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
        class SubForm(wtforms.Form):
            operation = wtforms.SelectField(choices=self.operations)
            query = wtforms.IntegerField()

        unbound_field: UnboundField = wtforms.FormField(SubForm, label=self.label)
        field = unbound_field.bind(form=None, name=self.query_param, _meta=DefaultMeta())
        field.process(formdata=None, data=self.get_value(request))
        macros = macro('ohmyadmin/filters.html', 'number_filter_field')
        return macros(field)

    def convert_value(self, value: str) -> typing.Any:
        return int(value)
