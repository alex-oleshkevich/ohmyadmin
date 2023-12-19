from __future__ import annotations

import abc
import typing

import wtforms
from starlette.requests import Request

from ohmyadmin.templating import render_to_string


class LayoutBuilder(typing.Protocol):
    def __call__(self, form: wtforms.Form | wtforms.Field) -> Layout:
        ...


class BaseLayoutBuilder(abc.ABC):
    def __call__(self, form: wtforms.Form) -> Layout:
        return self.build(form)

    @abc.abstractmethod
    def build(self, form: wtforms.Form | wtforms.Field) -> Layout:
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

    def __init__(
        self,
        children: list[Layout],
        label: str = "",
        description: str = "",
        colspan: int = 12,
    ) -> None:
        self.label = label
        self.colspan = colspan
        self.children = children
        self.description = description

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


class NestedFormLayout(Layout):
    template: str = "ohmyadmin/forms/layouts/nested_form.html"

    def __init__(self, field: wtforms.FormField, builder: LayoutBuilder) -> None:
        self.field = field
        self.builder = builder

    def render(self, request: Request) -> str:
        return render_to_string(
            request,
            self.template,
            {
                "layout": self,
                "field": self.field,
                "builder": self.builder,
            },
        )


class AutoLayout(BaseLayoutBuilder):
    def build(self, form: wtforms.Form | wtforms.Field) -> Layout:
        return GridLayout(
            columns=12,
            children=[self.build_for_field(field) for field in form],
        )

    def build_listfield_item(self, field: wtforms.Form) -> Layout:
        match field:
            case wtforms.FormField() as form_field:
                field_count = len(list(form_field))
                if field_count > 4:
                    return ColumnLayout(children=[FormInput(subfield) for subfield in form_field])
                return GridLayout(columns=field_count, children=[FormInput(subfield) for subfield in form_field])
            case _:
                return FormInput(field)

    def build_for_field(self, field: wtforms.Field) -> Layout:
        match field:
            case wtforms.FieldList() as list_field:
                return ColumnLayout(
                    colspan=8,
                    children=[
                        GroupLayout(
                            label=list_field.label.text,
                            description=list_field.description,
                            children=[
                                RepeatedFormInput(
                                    field=list_field,
                                    builder=lambda field: self.build_listfield_item(field),
                                )
                            ],
                        )
                    ],
                )
            case wtforms.TextAreaField():
                return GridLayout(children=[FormInput(field, colspan=6)])
            case wtforms.IntegerField() | wtforms.FloatField() | wtforms.DecimalField():
                return GridLayout(children=[FormInput(field, colspan=2)])
            case wtforms.FormField() as form_field:
                field_count = len(list(form_field))
                layout: Layout
                if field_count > 4:
                    layout = ColumnLayout(children=[FormInput(subfield) for subfield in form_field])
                layout = GridLayout(columns=field_count, children=[FormInput(subfield) for subfield in form_field])
                return GroupLayout(
                    colspan=8,
                    label=form_field.label.text,
                    description=form_field.description,
                    children=[NestedFormLayout(field=form_field, builder=lambda field: layout)],
                )
            case _:
                return GridLayout(children=[FormInput(field, colspan=4)])
