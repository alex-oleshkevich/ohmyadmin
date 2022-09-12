from starlette.requests import Request

from examples.models import Customer
from ohmyadmin.forms import DateField, EmailField, Form, TextField
from ohmyadmin.layout import Card, FormField, FormPlaceholder, Grid, Group, Layout
from ohmyadmin.resources import Resource
from ohmyadmin.tables import Column


class CustomerResource(Resource):
    icon = 'friends'
    entity_class = Customer
    table_columns = [
        Column('name', sortable=True, link=True, searchable=True),
        Column('email', sortable=True, searchable=True),
        Column('phone', searchable=True),
    ]
    form_fields = [
        TextField('name', required=True),
        EmailField('email', required=True),
        TextField('phone'),
        DateField('birthday'),
    ]

    def get_form_layout(self, request: Request, form: Form[Customer]) -> Layout:
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
                                FormField(form.email),
                                FormField(form.phone),
                                FormField(form.birthday),
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
