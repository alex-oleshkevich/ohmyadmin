from __future__ import annotations

import typing

import wtforms
from starlette.requests import Request

from ohmyadmin.components.base import Component
from ohmyadmin.components.text import Placeholder
from ohmyadmin.templating import render_to_string

F = typing.TypeVar("F", bound=wtforms.Form)
M = typing.TypeVar("M")


class FormView(Component, typing.Generic[F, M]):
    template_name = "ohmyadmin/components/forms/form_view.html"

    def __init__(self, form: F, model: M | None) -> None:
        self.form = form
        self.model = model

    def build(self, request: Request) -> Component:
        return Placeholder(message="This view does not define any content.")


class FormInput(Component):
    template_name: str = "ohmyadmin/components/forms/form_input.html"

    def __init__(self, field: wtforms.Field, colspan: int = 1) -> None:
        self.field = field
        self.colspan = colspan


class ImageFormInput(FormInput):
    template: str = "ohmyadmin/components/image_field.html"

    def __init__(self, field: wtforms.Field, media_url: str, colspan: int = 1) -> None:
        super().__init__(field, colspan)
        self.field = field
        self.colspan = colspan
        self.media_url = media_url


class FormLayoutBuilder(typing.Protocol):
    def __call__(self, field: wtforms.Field) -> Component:
        ...


class RepeatedFormInput(Component):
    template_name: str = "ohmyadmin/components/forms/repeated_form_input.html"

    def __init__(self, field: wtforms.FieldList, builder: FormLayoutBuilder) -> None:
        self.field = field
        self.builder = builder

    @property
    def template_field(self) -> Component:
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

        return self.builder(template_field)

    def render(self, request: Request) -> str:
        fields = [self.builder(field) for field in self.field]
        return render_to_string(
            request,
            self.template_name,
            {
                "component": self,
                "fields": fields,
            },
        )


class NestedFormComponent(Component):
    template: str = "ohmyadmin/components/nested_form.html"

    def __init__(self, field: wtforms.FormField, builder: "FormLayoutBuilder") -> None:
        self.field = field
        self.builder = builder
