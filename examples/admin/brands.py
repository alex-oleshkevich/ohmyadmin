from starlette.requests import Request

from examples.models import Brand
from ohmyadmin.components import Card, Component, FormElement, FormPlaceholder, Grid, Group
from ohmyadmin.old_forms import CheckboxField, Form, MarkdownField, SlugField, TextField
from ohmyadmin.resources import Resource
from ohmyadmin.tables import BoolColumn, Column, DateColumn


class EditForm(Form):
    name = TextField(required=True)
    slug = SlugField(required=True)
    website = TextField()
    visible_to_customers = CheckboxField()
    description = MarkdownField()


class BrandResource(Resource):
    icon = 'basket'
    entity_class = Brand
    form_class = EditForm
    table_columns = [
        Column('name', searchable=True, sortable=True, link=True),
        Column('website'),
        BoolColumn('visible_to_customers', label='Visibility'),
        DateColumn('updated_at'),
    ]

    def get_form_layout(self, request: Request, form: Form[Brand]) -> Component:
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
                                FormElement(form.website),
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
