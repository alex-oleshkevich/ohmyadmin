from __future__ import annotations

import abc
import typing

import wtforms
from starlette.requests import Request

from ohmyadmin.templating import render_to_string


class LayoutBuilder(typing.Protocol):
    def __call__(self, form: wtforms.Form) -> Layout:
        ...


class BaseLayoutBuilder(abc.ABC):
    def __call__(self, form: wtforms.Form) -> Layout:
        return self.build(form)

    @abc.abstractmethod
    def build(self, form: wtforms.Form) -> Layout:
        raise NotImplementedError()


class Layout(abc.ABC):
    def render(self, request: Request) -> str:
        raise NotImplementedError()


class FormInput(Layout):
    template: str = "ohmyadmin/forms/layouts/field.html"

    def __init__(self, field: wtforms.Field, colspan: int = 1) -> None:
        self.field = field
        self.colspan = colspan

    def render(self, request: Request) -> str:
        return render_to_string(
            request,
            self.template,
            {
                "layout": self,
                "field": self.field,
            },
        )


class ColumnLayout(Layout):
    template: str = "ohmyadmin/forms/layouts/column.html"

    def __init__(self, children: list[Layout], columns: int = 1, gap: int = 5, colspan: int = 12) -> None:
        self.gap = gap
        self.colspan = colspan
        self.columns = columns
        self.children = children

    def render(self, request: Request) -> str:
        return render_to_string(
            request,
            self.template,
            {
                "layout": self,
                "children": self.children,
            },
        )


class GridLayout(Layout):
    template: str = "ohmyadmin/forms/layouts/grid.html"

    def __init__(self, children: list[Layout], columns: int = 12, gap: int = 5, colspan: int = 12) -> None:
        self.gap = gap
        self.colspan = colspan
        self.columns = columns
        self.children = children

    def render(self, request: Request) -> str:
        return render_to_string(
            request,
            self.template,
            {
                "layout": self,
                "children": self.children,
            },
        )


class GroupLayout(Layout):
    template: str = "ohmyadmin/forms/layouts/group.html"

    def __init__(self, children: list[Layout], label: str = "", description: str = "") -> None:
        self.label = label
        self.description = description
        self.children = children

    def render(self, request: Request) -> str:
        return render_to_string(
            request,
            self.template,
            {
                "layout": self,
                "children": self.children,
            },
        )


class RepeatedFormInput(Layout):
    template: str = "ohmyadmin/forms/layouts/repeated_form_input.html"

    def __init__(self, field: wtforms.FieldList, builder: LayoutBuilder) -> None:
        self.field = field
        self.builder = builder

    def render(self, request: Request) -> str:
        template_field = self.field.append_entry()
        last_index = self.field.last_index
        self.field.pop_entry()

        def patch_field(field: wtforms.Field) -> None:
            field.render_kw = field.render_kw or {}
            field.render_kw.update(
                {
                    ":id": "`" + field.id.replace(str(last_index), "${index}") + "`",
                    ":name": "`" + field.name.replace(str(last_index), "${index}") + "`",
                }
            )

        try:
            for subfield in template_field:
                patch_field(subfield)
        except TypeError:
            patch_field(template_field)

        return render_to_string(
            request,
            self.template,
            {
                "layout": self,
                "field": self.field,
                "builder": self.builder,
                "template_field": template_field,
            },
        )


class VerticalLayout(BaseLayoutBuilder):
    def build(self, form: wtforms.Form) -> Layout:
        return GridLayout(
            children=[
                ColumnLayout(
                    colspan=6,
                    children=[FormInput(field) for field in form],
                )
            ],
            columns=12,
        )
