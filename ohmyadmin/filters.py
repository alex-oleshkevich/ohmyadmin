from __future__ import annotations

import dataclasses

import abc
import sqlalchemy as sa
import typing
from sqlalchemy.orm import InstrumentedAttribute
from starlette.requests import Request

from ohmyadmin.components import Component, FormElement, Grid
from ohmyadmin.forms import Form
from ohmyadmin.helpers import render_to_string
from ohmyadmin.tables import Column, get_ordering_value, get_search_value


class EmptyForm(Form):
    ...


@dataclasses.dataclass
class FilterIndicator:
    label: str
    value: str
    query_param: str

    def render(self, request: Request) -> str:
        return render_to_string('ohmyadmin/tables/filter_indicator.html', {'indicator': self, 'request': request})


class BaseFilter(abc.ABC):
    label: str = ''
    has_ui: bool = True
    form_class: typing.ClassVar[typing.Type[Form]] = EmptyForm
    _layout: Component | None = None
    _indicators: typing.Iterable[FilterIndicator] | None = None

    @property
    def indicators(self) -> typing.Iterable[FilterIndicator]:
        assert self._indicators, f'{self.__class__.__name__} is not initialized. Did you call dispatch() method?'
        return self._indicators

    async def dispatch(self, request: Request, stmt: sa.sql.Select) -> sa.sql.Select:
        form = await self.get_form_class().from_request(request, form_data=request.query_params)
        self._layout = Grid(columns=1, children=[FormElement(field) for field in form])
        self._indicators = self.get_indicators(form)
        return self.apply(request, stmt, form)

    def get_indicators(self, form: Form) -> typing.Iterable[FilterIndicator]:
        for field in form:
            if field.data:
                yield FilterIndicator(label=field.label.text, value=str(field.data), query_param=field.name)

    @abc.abstractmethod
    def apply(self, request: Request, queryset: sa.sql.Select, form: Form) -> sa.sql.Select:
        ...

    def render(self) -> str:
        assert self._layout, f'{self.__class__.__name__} is not initialized. Did you call dispatch() method?'
        return str(self._layout)

    def get_form_class(self) -> typing.Type[Form]:
        form_class = getattr(self, 'FilterForm', self.form_class)
        assert form_class, f'{self.__class__.__name__} does not define form.'
        return form_class

    def __str__(self) -> str:
        return self.render()


class OrderingFilter(BaseFilter):
    has_ui = False

    def __init__(self, entity_class: typing.Any, columns: typing.Iterable[Column], query_param: str) -> None:
        self.entity_class = entity_class
        self.query_param = query_param
        self.columns = {
            column.get_sorting_key(): column.sort_by if column.sort_by else getattr(entity_class, column.name)
            for column in columns
        }

    def apply(self, request: Request, queryset: sa.sql.Select, form: Form) -> sa.sql.Select:
        ordering = get_ordering_value(request, self.query_param)
        if ordering:
            queryset = queryset.order_by(None)

        for order in ordering:
            field_name = order.lstrip('-')
            if field_name not in self.columns:
                continue

            column = self.columns[field_name]
            queryset = queryset.order_by(sa.desc(column) if order.startswith('-') else column)
        return queryset


class SearchFilter(BaseFilter):
    has_ui = False

    def __init__(self, entity_class: typing.Any, columns: typing.Iterable[Column], query_param: str) -> None:
        self.entity_class = entity_class
        self.query_param = query_param
        self.db_columns: list[InstrumentedAttribute] = []
        for column in columns:
            self.db_columns.extend(column.search_in or [getattr(entity_class, column.name)])

    def create_search_token(self, column: InstrumentedAttribute, search_query: str) -> sa.sql.ColumnElement:
        string_column = sa.cast(column, sa.Text)
        if search_query.startswith('^'):
            search_token = f'{search_query[1:].lower()}%'
            return string_column.ilike(search_token)

        if search_query.startswith('='):
            search_token = f'{search_query[1:].lower()}'
            return sa.func.lower(string_column) == search_token

        if search_query.startswith('@'):
            search_token = f'{search_query[1:].lower()}'
            return string_column.regexp_match(search_token)

        search_token = f'%{search_query.lower()}%'
        return string_column.ilike(search_token)

    def apply(self, request: Request, queryset: sa.sql.Select, form: Form) -> sa.sql.Select:
        search_query = get_search_value(request, self.query_param)
        if not search_query:
            return queryset

        clauses = []
        for column in self.db_columns:
            clause = self.create_search_token(column, search_query)
            clauses.append(clause)

        if clauses:
            queryset = queryset.where(sa.or_(*clauses))

        return queryset
