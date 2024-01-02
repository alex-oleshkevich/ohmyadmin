from __future__ import annotations

import abc
import contextvars
import decimal
import functools
import typing

import wtforms
from starlette.datastructures import URL
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

from ohmyadmin.datasources import datasource
from ohmyadmin.datasources.datasource import DataSource, DateOperation, NumberFilter, NumberOperation
from ohmyadmin.forms.utils import create_form, safe_enum_coerce
from ohmyadmin.helpers import snake_to_sentence
from ohmyadmin.ordering import get_ordering_value

F = typing.TypeVar("F", bound=wtforms.Form)


class Filter(abc.ABC, typing.Generic[F]):
    visible_in_toolbar: bool = True
    form_class: typing.Type[F] = wtforms.Form
    template: str = "ohmyadmin/filters/form.html"
    indicator_template: str = "ohmyadmin/filters/blank_indicator.html"

    def __init__(self, field_name: str, label: str = "", *, filter_id: str = "") -> None:
        self.field_name = field_name
        self.filter_id = filter_id or field_name
        self.label = label or snake_to_sentence(self.field_name.title())
        self._form_instance: contextvars.ContextVar[F] = contextvars.ContextVar(f"_local_form_{filter_id}")

    async def get_form(self, request: Request) -> F:
        try:
            return self._form_instance.get()
        except LookupError:
            form = await create_form(request, self.form_class, form_data=request.query_params, prefix=self.filter_id)
            self._form_instance.set(form)
        return self._form_instance.get()

    def get_indicator_context(self) -> typing.Mapping[str, typing.Any]:
        return self.form.data

    def get_reset_url(self, request: Request) -> URL:
        return request.url.remove_query_params([field.name for field in self.form])

    @property
    def form(self) -> F:
        return self._form_instance.get()

    @abc.abstractmethod
    def apply(self, request: Request, query: DataSource, form: wtforms.Form) -> DataSource:
        """Apply filter to the data source query."""

    @abc.abstractmethod
    def is_active(self, request: Request) -> bool:
        """
        Check if the filter is active.

        Active filters rendered differently in the filter bar.
        """


class SearchFilter(Filter):
    visible_in_toolbar = False

    def __init__(self, model_fields: typing.Sequence[str], field_name: str = "search") -> None:
        super().__init__(field_name=field_name)
        self.model_fields = model_fields

    def apply(self, request: Request, query: DataSource, form: wtforms.Form) -> DataSource:
        value = request.query_params.get(self.field_name, "")
        if not value:
            return query

        if value.startswith("^"):
            return query.filter(
                datasource.OrFilter(
                    [
                        datasource.StringFilter(
                            field=field,
                            value=value[1:],
                            predicate=datasource.StringOperation.STARTSWITH,
                            case_insensitive=True,
                        )
                        for field in self.model_fields
                    ]
                )
            )
        if value.startswith("="):
            return query.filter(
                datasource.OrFilter(
                    [
                        datasource.StringFilter(
                            field=field,
                            value=value[1:],
                            predicate=datasource.StringOperation.EXACT,
                            case_insensitive=True,
                        )
                        for field in self.model_fields
                    ]
                )
            )
        if value.startswith("$"):
            return query.filter(
                datasource.OrFilter(
                    [
                        datasource.StringFilter(
                            field=field,
                            value=value[1:],
                            predicate=datasource.StringOperation.ENDSWITH,
                            case_insensitive=True,
                        )
                        for field in self.model_fields
                    ]
                )
            )
        if value.startswith("@"):
            return query.filter(
                datasource.OrFilter(
                    [
                        datasource.StringFilter(
                            field=field,
                            value=value[1:],
                            predicate=datasource.StringOperation.MATCHES,
                            case_insensitive=True,
                        )
                        for field in self.model_fields
                    ]
                )
            )

        return query.filter(
            datasource.OrFilter(
                [
                    datasource.StringFilter(
                        field=field, value=value, predicate=datasource.StringOperation.CONTAINS, case_insensitive=True
                    )
                    for field in self.model_fields
                ]
            )
        )

    def is_active(self, request: Request) -> bool:
        return False


class OrderingFilter(Filter):
    visible_in_toolbar = False

    def __init__(self, model_fields: typing.Sequence[str], field_name: str = "ordering") -> None:
        super().__init__(field_name=field_name)
        self.model_fields = model_fields

    def apply(self, request: Request, query: DataSource, form: wtforms.Form) -> DataSource:
        ordering = get_ordering_value(request, self.field_name)
        return query.order_by({k: v for k, v in ordering.items() if k in self.model_fields})

    def is_active(self, request: Request) -> bool:
        return False


class StringFilterForm(wtforms.Form):
    predicate = wtforms.SelectField(
        _("Predicate"),
        choices=datasource.StringOperation.choices(),
        coerce=functools.partial(safe_enum_coerce, choices=datasource.StringOperation),
    )
    query = wtforms.StringField(render_kw={"autofocus": "on"})


class StringFilter(Filter[StringFilterForm]):
    form_class = StringFilterForm
    indicator_template = "ohmyadmin/filters/enum_indicator.html"

    def apply(self, request: Request, query: DataSource, form: StringFilterForm) -> DataSource:
        operation = form.data["predicate"]
        value = form.data["query"]
        if not operation or not value:
            return query

        return query.filter(datasource.StringFilter(self.field_name, value, operation, case_insensitive=True))

    def is_active(self, request: Request) -> bool:
        return bool(self.form.query.data)


class IntegerFilterForm(wtforms.Form):
    predicate = wtforms.SelectField(
        choices=NumberOperation.choices(),
        coerce=functools.partial(safe_enum_coerce, choices=NumberOperation),
    )
    query = wtforms.IntegerField()


class IntegerFilter(Filter[IntegerFilterForm]):
    form_class = IntegerFilterForm
    indicator_template = "ohmyadmin/filters/enum_indicator.html"

    def apply(self, request: Request, query: DataSource, form: IntegerFilterForm) -> DataSource:
        predicate = form.data["predicate"]
        value = self.form.data["query"]
        if not predicate or value is None:
            return query

        return query.filter(NumberFilter(self.field_name, value, predicate))

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data["query"])


class FloatFilterForm(wtforms.Form):
    predicate = wtforms.SelectField(
        choices=NumberOperation.choices(),
        coerce=functools.partial(safe_enum_coerce, choices=NumberOperation),
    )
    query = wtforms.FloatField()


class FloatFilter(IntegerFilter, Filter[FloatFilterForm]):
    form_class = FloatFilterForm


class DecimalFilterForm(wtforms.Form):
    predicate = wtforms.SelectField(
        choices=NumberOperation.choices(),
        coerce=functools.partial(safe_enum_coerce, choices=NumberOperation),
    )
    query = wtforms.DecimalField()


class DecimalFilter(IntegerFilter, Filter[FloatFilterForm]):
    form_class = DecimalFilterForm


class DateFilterForm(wtforms.Form):
    predicate = wtforms.SelectField(
        choices=DateOperation.choices(),
        coerce=functools.partial(safe_enum_coerce, choices=DateOperation),
    )
    query = wtforms.DateField()


class DateFilter(Filter[DateFilterForm]):
    form_class = DateFilterForm
    indicator_template = "ohmyadmin/filters/date_indicator.html"

    def apply(self, request: Request, query: DataSource, form: wtforms.Form) -> DataSource:
        predicate = self.form.data["predicate"]
        value = self.form.data["query"]
        if value is None or predicate is None:
            return query
        return query.filter(datasource.DateFilter(self.field_name, value, predicate))

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data["query"])


class DateTimeFilterForm(wtforms.Form):
    predicate = wtforms.SelectField(
        choices=DateOperation.choices(),
        coerce=functools.partial(safe_enum_coerce, choices=DateOperation),
    )
    query = wtforms.DateTimeLocalField()


class DateTimeFilter(DateFilter, Filter[DateFilterForm]):
    form_class = DateTimeFilterForm
    indicator_template = "ohmyadmin/filters/datetime_indicator.html"


class DateRangeFilterForm(wtforms.Form):
    after = wtforms.DateField()
    before = wtforms.DateField()


class DateRangeFilter(Filter[DateRangeFilterForm]):
    form_class = DateRangeFilterForm
    format: typing.Literal["date", "datetime"] = "date"
    indicator_template = "ohmyadmin/filters/date_range_indicator.html"

    def apply(self, request: Request, query: DataSource, form: DateTimeFilterForm) -> DataSource:
        before = self.form.data["before"]
        after = self.form.data["after"]
        if before and after:
            return query.filter(
                datasource.AndFilter(
                    filters=[
                        datasource.DateFilter(self.field_name, before, datasource.DateOperation.BEFORE),
                        datasource.DateFilter(self.field_name, after, datasource.DateOperation.AFTER),
                    ]
                )
            )
        if before:
            return query.filter(datasource.DateFilter(self.field_name, before, datasource.DateOperation.BEFORE))
        if after:
            return query.filter(datasource.DateFilter(self.field_name, after, datasource.DateOperation.AFTER))
        return query

    def is_active(self, request: Request) -> bool:
        return self.form.data["before"] or self.form.data["after"]


class DateTimeRangeFilterForm(wtforms.Form):
    after = wtforms.DateTimeLocalField()
    before = wtforms.DateTimeLocalField()


class DateTimeRangeFilter(DateRangeFilter, Filter[DateTimeRangeFilterForm]):
    form_class = DateTimeRangeFilterForm
    format: typing.Literal["date", "datetime"] = "datetime"


class ChoiceFilterForm(wtforms.Form):
    choice = wtforms.SelectField(label=_("Choices", domain="ohmyadmin"), choices=[])


ChoiceLoader: typing.TypeAlias = typing.Callable[[Request], typing.Awaitable[list[tuple[typing.Any, str]]]]


class ChoiceFilter(Filter[ChoiceFilterForm]):
    form_class = ChoiceFilterForm
    indicator_template = "ohmyadmin/filters/choice_indicator.html"

    def __init__(
        self,
        query_param: str,
        label: str = "",
        filter_id: str = "",
        *,
        choices: typing.Any | ChoiceLoader,
        coerce: type[str | int | float | decimal.Decimal] = str,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(query_param, label, filter_id=filter_id, **kwargs)
        self.coerce = coerce
        self.choices = choices

    async def get_form(self, request: Request) -> ChoiceFilterForm:
        choices = self.choices
        if callable(self.choices):
            choices = await self.choices(request)

        form: ChoiceFilterForm = await super().get_form(request)
        form.choice.coerce = self.coerce
        form.choice.choices = [("", ""), *choices]
        return form

    def apply(self, request: Request, query: DataSource, form: ChoiceFilterForm) -> DataSource:
        choice = form.choice.data
        if choice:
            return query.filter(datasource.InFilter(self.field_name, [self.coerce(choice)]))
        return query

    def is_active(self, request: Request) -> bool:
        return bool(self.form.data["choice"])

    def get_indicator_context(self) -> dict[str, typing.Any]:
        value = self.form.data
        by_key = {choice[0]: choice[1] for choice in self.form.choice.choices}
        choice = by_key.get(self.coerce(value["choice"]), "")
        return {"value": choice}


class MultiChoiceFilterForm(wtforms.Form):
    choice = wtforms.SelectMultipleField(label=_("Select multiple", domain="ohmyadmin"), choices=[])


class MultiChoiceFilter(Filter[MultiChoiceFilterForm]):
    form_class = MultiChoiceFilterForm
    indicator_template = "ohmyadmin/filters/multi_choice_indicator.html"

    def __init__(
        self,
        query_param: str,
        label: str = "",
        filter_id: str = "",
        *,
        choices: typing.Any,
        coerce: type[str | int | float | decimal.Decimal] = str,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(query_param, label, filter_id=filter_id, **kwargs)
        self.coerce = coerce
        self.choices = choices

    async def get_form(self, request: Request) -> ChoiceFilterForm:
        form: ChoiceFilterForm = await super().get_form(request)
        form.choice.coerce = self.coerce
        form.choice.choices = self.choices
        return form

    def apply(self, request: Request, query: DataSource, form: MultiChoiceFilterForm) -> DataSource:
        if self.is_active(request):
            return query.filter(
                datasource.InFilter(
                    field=self.field_name, values=[self.coerce(value) for value in self.form.choice.data]
                )
            )
        return query

    def is_active(self, request: Request) -> bool:
        if self.form.validate():
            return bool(self.form.data["choice"])
        return False

    def get_indicator_context(self) -> dict[str, typing.Any]:
        value = self.form.choice.data
        choices = (choice for choice in self.form.choice.choices if choice[0] in value)
        values = [choice[1] for choice in choices]
        return {"value": values}
