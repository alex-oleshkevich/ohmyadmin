from __future__ import annotations

import abc
import typing

import wtforms
from markupsafe import Markup
from starlette.datastructures import URL
from starlette.requests import Request

from ohmyadmin import formatters
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.routing import LazyURL
from ohmyadmin.templating import render_to_string


class Component(abc.ABC):
    def render(self, request: Request) -> str:
        raise NotImplementedError()


class FormInput(Component):
    template: str = "ohmyadmin/components/field.html"

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


class ImageFormInput(FormInput):
    template: str = "ohmyadmin/components/image_field.html"

    def __init__(self, field: wtforms.Field, media_url: str, colspan: int = 1) -> None:
        super().__init__(field, colspan)
        self.field = field
        self.colspan = colspan
        self.media_url = media_url


class Column(Component):
    template: str = "ohmyadmin/components/column.html"

    def __init__(self, children: list[Component], gap: int = 3, colspan: int = 12) -> None:
        self.gap = gap
        self.colspan = colspan
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


class Grid(Component):
    template: str = "ohmyadmin/components/grid.html"

    def __init__(self, children: list[Component], columns: int = 12, gap: int = 5, colspan: int = 12) -> None:
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


class Group(Component):
    template: str = "ohmyadmin/components/group.html"

    def __init__(
        self,
        children: list[Component],
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


class RepeatedFormInput(Component):
    template: str = "ohmyadmin/components/repeated_form_input.html"

    def __init__(self, field: wtforms.FieldList, builder: FormLayoutBuilder) -> None:
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


class NestedFormComponent(Component):
    template: str = "ohmyadmin/components/nested_form.html"

    def __init__(self, field: wtforms.FormField, builder: FormLayoutBuilder) -> None:
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


class TextComponent(Component):
    template: str = "ohmyadmin/components/text.html"

    def __init__(
        self,
        value: typing.Any,
        formatter: formatters.FieldValueFormatter = formatters.StringFormatter(),
    ) -> None:
        self.value = value
        self.formatter = formatter

    def render(self, request: Request) -> str:
        return render_to_string(
            request,
            self.template,
            {
                "layout": self,
                "value": self.value,
                "formatted_value": self.formatter(request, self.value),
            },
        )


class RawHTMLComponent(Component):
    def __init__(self, content: str) -> None:
        self.content = Markup(content)

    def render(self, request: Request) -> str:
        return self.content


class SeparatorComponent(Component):
    def render(self, request: Request) -> str:
        return RawHTMLComponent("<hr>").render(request)


class Image(Component):
    template: str = "ohmyadmin/components/image.html"

    def __init__(self, src: str) -> None:
        self.src = src

    def render(self, request: Request) -> str:
        return render_to_string(
            request,
            self.template,
            {
                "layout": self,
                "src": self.src,
            },
        )


class DisplayValue(Component):
    def __init__(
        self,
        label: str,
        value: typing.Any,
        formatter: formatters.FieldValueFormatter = formatters.StringFormatter(),
    ) -> None:
        self.label = label
        self.value = value
        self.formatter = formatter

    def render(self, request: Request) -> str:
        layout = Grid(
            columns=12,
            children=[
                Column(children=[TextComponent(value=self.label)], colspan=4),
                Column(children=[TextComponent(value=self.formatter(request, self.value))], colspan=8),
            ],
        )
        return layout.render(request)


class DisplayFieldComponent(Component):
    def __init__(self, field: DisplayField, model: typing.Any) -> None:
        self.field = field
        self.model = model

    def render(self, request: Request) -> str:
        component = DisplayValue(
            label=self.field.label,
            value=self.field.get_field_value(request, self.model),
        )
        return component.render(request)


class FormLayoutBuilder(typing.Protocol):
    def __call__(self, form: wtforms.Form | wtforms.Field) -> Component:
        ...


class BaseFormLayoutBuilder(abc.ABC):
    def __call__(self, form: wtforms.Form) -> Component:
        return self.build(form)

    @abc.abstractmethod
    def build(self, form: wtforms.Form | wtforms.Field) -> Component:
        raise NotImplementedError()


class AutoFormLayout(BaseFormLayoutBuilder):
    def build(self, form: wtforms.Form | wtforms.Field) -> Component:
        return Grid(
            columns=12,
            children=[self.build_for_field(field) for field in form],
        )

    def build_listfield_item(self, field: wtforms.Form) -> Component:
        match field:
            case wtforms.FormField() as form_field:
                field_count = len(list(form_field))
                if field_count > 4:
                    return Column(children=[FormInput(subfield) for subfield in form_field])
                return Grid(columns=field_count, children=[FormInput(subfield) for subfield in form_field])
            case _:
                return FormInput(field)

    def build_for_field(self, field: wtforms.Field) -> Component:
        match field:
            case wtforms.FieldList() as list_field:
                return Column(
                    colspan=8,
                    children=[
                        Group(
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
                return Grid(children=[FormInput(field, colspan=6)])
            case wtforms.IntegerField() | wtforms.FloatField() | wtforms.DecimalField():
                return Grid(children=[FormInput(field, colspan=2)])
            case wtforms.FormField() as form_field:
                field_count = len(list(form_field))
                layout: Component
                if field_count > 4:
                    layout = Column(children=[FormInput(subfield) for subfield in form_field])
                layout = Grid(columns=field_count, children=[FormInput(subfield) for subfield in form_field])
                return Group(
                    colspan=8,
                    label=form_field.label.text,
                    description=form_field.description,
                    children=[NestedFormComponent(field=form_field, builder=lambda field: layout)],
                )
            case _:
                return Grid(children=[FormInput(field, colspan=4)])


class DisplayLayoutBuilder(typing.Protocol):
    def __call__(self, request: Request, model: typing.Any) -> Component:
        ...


class BaseDisplayLayoutBuilder(abc.ABC):
    def __call__(self, request: Request, model: typing.Any) -> Component:
        return self.build(request, model)

    @abc.abstractmethod
    def build(self, request: Request, model: typing.Any) -> Component:
        raise NotImplementedError()


class AutoDisplayLayout(BaseDisplayLayoutBuilder):
    def build(self, request: Request, model: typing.Any) -> Component:
        fields = request.state.resource.display_fields
        return Grid(
            columns=12,
            children=[
                Column(
                    colspan=6,
                    children=[DisplayFieldComponent(field=field, model=model) for field in fields],
                )
            ],
        )


class MenuItem(Component):
    template = 'ohmyadmin/components/menu_item.html'

    def __init__(self, url: str | URL | LazyURL, label: str, icon: str = '', badge: str = '') -> None:
        self.url = URL(url) if isinstance(str, URL) else url
        self.label = label
        self.icon = icon
        self.badge = badge

    def resolve_url(self, request: Request) -> URL:
        match self.url:
            case URL():
                return self.url
            case LazyURL():
                return self.url.resolve(request)
            case _:
                return URL(self.url)

    def is_active(self, request: Request) -> bool:
        url = self.resolve_url(request)
        return request.url.path.startswith(url.path)

    def render(self, request: Request) -> str:
        return render_to_string(request, self.template, {
            'component': self,
        })


class MenuHeading(Component):
    template = 'ohmyadmin/components/menu_heading.html'

    def __init__(self, label: str) -> None:
        self.label = label

    def render(self, request: Request) -> str:
        return render_to_string(request, self.template, {
            'component': self,
        })


class MenuGroup(Component):
    template = 'ohmyadmin/components/menu.html'

    def __init__(self, items: typing.Sequence[Component], heading: str = '') -> None:
        self.heading = heading
        self.items = list(items)

    def render(self, request: Request) -> str:
        items = self.items
        if self.heading:
            items.insert(0, MenuHeading(self.heading))

        return render_to_string(request, self.template, {
            'component': self,
            'items': items,
        })


class Menu(Component):
    def __init__(self, builder: typing.Callable[[Request], Component]) -> None:
        self.builder = builder

    def render(self, request: Request) -> str:
        return self.builder(request).render(request)
