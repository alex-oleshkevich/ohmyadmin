import typing
import wtforms
from starlette.requests import Request

from examples.models import Category
from ohmyadmin.components import Card, Component, FormElement, FormPlaceholder, Grid, Group, display
from ohmyadmin.components.display import DisplayField
from ohmyadmin.ext.sqla import SQLAlchemyResource, choices_from
from ohmyadmin.forms import BooleanField, Form, MarkdownField, SelectField, SlugField, StringField


def safe_int(value: int | str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


class CategoryResource(SQLAlchemyResource):
    icon = 'category'
    entity_class = Category

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        yield DisplayField('name', searchable=True, sortable=True, link=True)
        yield DisplayField('visible_to_customers', label='Visilibity', component=display.Boolean())
        yield DisplayField('updated_at', component=display.DateTime())

    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        yield StringField(name='name', validators=[wtforms.validators.data_required()])
        yield SlugField(name='slug', validators=[wtforms.validators.data_required()])
        yield SelectField(name='parent_id', choices=choices_from(Category), coerce=safe_int)
        yield BooleanField(name='visible_to_customers')
        yield MarkdownField(name='description')

    def get_form_layout(self, request: Request, form: Form) -> Component:
        return Grid(
            columns=3,
            children=[
                Group(
                    colspan=2,
                    children=[
                        Card(
                            columns=2,
                            children=[
                                FormElement(form.name),
                                FormElement(form.slug),
                                FormElement(form.parent, colspan=2),
                                FormElement(form.visible_to_customers),
                                FormElement(form.description, colspan=2),
                            ],
                        )
                    ],
                ),
                Group(
                    colspan=1,
                    children=[
                        Card(
                            children=[
                                FormPlaceholder(
                                    'Created at',
                                    (
                                        form.instance.created_at.date().isoformat()
                                        if form.instance and form.instance.created_at
                                        else '-'
                                    ),
                                ),
                                FormPlaceholder(
                                    'Updated at',
                                    (
                                        form.instance.updated_at.date().isoformat()
                                        if form.instance and form.instance.updated_at
                                        else '-'
                                    ),
                                ),
                            ]
                        )
                    ],
                ),
            ],
        )
