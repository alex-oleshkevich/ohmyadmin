from starlette.requests import Request

from examples.models import Customer
from ohmyadmin.forms import DateField, EmailField, Form, TextField
from ohmyadmin.layout import Card, FormElement, FormPlaceholder, Grid, Group, Layout
from ohmyadmin.resources import Resource
from ohmyadmin.tables import Column


class EditForm(Form):
    name = TextField(required=True)
    email = EmailField(required=True)
    phone = TextField()
    birthday = DateField()


class CustomerResource(Resource):
    icon = 'friends'
    entity_class = Customer
    form_class = EditForm
    table_columns = [
        Column('name', sortable=True, link=True, searchable=True),
        Column('email', sortable=True, searchable=True),
        Column('phone', searchable=True),
    ]

    def get_form_layout(self, request: Request, form: Form[Customer]) -> Layout:
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
                                FormElement(form.email),
                                FormElement(form.phone),
                                FormElement(form.birthday),
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
