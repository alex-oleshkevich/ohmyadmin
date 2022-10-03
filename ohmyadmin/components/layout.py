from __future__ import annotations

import abc
import datetime
import typing
import wtforms
from starlette.requests import Request

from ohmyadmin.templating import macro


def name_to_field(field_name: str, form: wtforms.Form) -> wtforms.Field:
    return getattr(form, field_name)


def resolve_lazy_fields(fields: list[str | LayoutComponent]) -> list[LayoutComponent]:
    return [FormElement(field) if isinstance(field, str) else field for field in fields]


class LayoutComponent:
    @abc.abstractmethod
    def render(self, request: Request, form: wtforms.Form) -> str:
        ...

    def __call__(self, request: Request, form: wtforms.Form) -> str:
        return self.render(request, form)


class FormElement(LayoutComponent):
    def __init__(self, field: wtforms.Field | str, max_width: str = '', colspan: str | int = '') -> None:
        self.field = field
        self.colspan = colspan
        self.max_width = max_width

    def render(self, request: Request, form: wtforms.Form) -> str:
        if isinstance(self.field, str):
            self.field = form[self.field]

        macros = macro('ohmyadmin/form_layout.html', 'field')
        return macros(request=request, form=form, component=self)

    def __repr__(self) -> str:
        return f'FormElement(field={repr(self.field)})'


class Grid(LayoutComponent):
    def __init__(self, children: list[LayoutComponent | str], columns: int = 1, gap: int = 5) -> None:
        self.children = resolve_lazy_fields(children)
        self.columns = columns
        self.gap = gap

    def render(self, request: Request, form: wtforms.Form) -> str:
        macros = macro('ohmyadmin/form_layout.html', 'grid')
        return macros(request=request, form=form, component=self)

    def __iter__(self) -> typing.Iterator[LayoutComponent]:
        yield from self.children


class Card(LayoutComponent):
    def __init__(self, children: list[LayoutComponent | str], label: str = '', columns: int = 1, gap: int = 5) -> None:
        self.children = resolve_lazy_fields(children)
        self.columns = columns
        self.gap = gap
        self.label = label

    def render(self, request: Request, form: wtforms.Form) -> str:
        macros = macro('ohmyadmin/form_layout.html', 'card')
        return macros(request=request, form=form, component=self)

    def __iter__(self) -> typing.Iterator[LayoutComponent]:
        yield from self.children


class Group(LayoutComponent):
    def __init__(
        self,
        children: list[LayoutComponent | str],
        colspan: str | int = 'full',
        columns: int = 1,
        gap: int = 5,
    ) -> None:
        self.gap = gap
        self.columns = columns
        self.colspan = colspan
        self.children = resolve_lazy_fields(children)

    def render(self, request: Request, form: wtforms.Form) -> str:
        macros = macro('ohmyadmin/form_layout.html', 'group')
        return macros(request=request, form=form, component=self)

    def __iter__(self) -> typing.Iterator[LayoutComponent]:
        yield from self.children


class Text(LayoutComponent):
    def __init__(self, text: str | None) -> None:
        self.text = text or ''

    def render(self, request: Request, form: wtforms.Form) -> str:
        return self.text


class Date(LayoutComponent):
    def __init__(
        self,
        date: datetime.date | datetime.datetime | None,
        empty_value: str = '-',
        format: str = '%d %B, %Y',
    ) -> None:
        self.value = date
        self.format = format
        self.empty_value = empty_value

    def render(self, request: Request, form: wtforms.Form) -> str:
        if self.value:
            return self.value.strftime(self.format)
        return self.empty_value


class FormText(LayoutComponent):
    def __init__(self, label: str, component: LayoutComponent) -> None:
        self.label = label
        self.component = component

    def render(self, request: Request, form: wtforms.Form) -> str:
        macros = macro('ohmyadmin/form_layout.html', 'form_text')
        return macros(request=request, form=form, component=self)
