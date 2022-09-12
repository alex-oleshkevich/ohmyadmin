from starlette.requests import Request

from examples.models import Brand
from ohmyadmin.forms import (
    Card,
    CheckboxField,
    Form,
    FormField,
    FormPlaceholder,
    Grid,
    Group,
    Layout,
    MarkdownField,
    SlugField,
    TextField,
)
from ohmyadmin.resources import Resource
from ohmyadmin.tables import BoolColumn, Column, DateColumn


class BrandResource(Resource):
    icon = 'basket'
    entity_class = Brand
    table_columns = [
        Column('name', searchable=True, sortable=True, link=True),
        Column('website'),
        BoolColumn('visible_to_customers', label='Visibility'),
        DateColumn('updated_at'),
    ]
    form_fields = [
        TextField('name', required=True),
        SlugField('slug', required=True),
        TextField('website'),
        CheckboxField('visible_to_customers'),
        MarkdownField('description'),
    ]

    def get_form_layout(self, request: Request, form: Form[Brand]) -> Layout:
        return Grid(
            cols=3,
            children=[
                Group(
                    colspan=2,
                    children=[
                        Card(
                            columns=2,
                            children=[
                                FormField(form.name),
                                FormField(form.slug),
                                FormField(form.website),
                                FormField(form.visible_to_customers),
                                FormField(form.description, colspan=2),
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
                                    (form.instance.created_at.date().isoformat() if form.instance.created_at else '-'),
                                ),
                                FormPlaceholder(
                                    'Updated at',
                                    (form.instance.updated_at.date().isoformat() if form.instance.updated_at else '-'),
                                ),
                            ]
                        )
                    ],
                ),
            ],
        )
