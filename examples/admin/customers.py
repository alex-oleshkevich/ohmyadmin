from __future__ import annotations

import sqlalchemy as sa
from starlette.requests import Request

from examples.models import Customer
from ohmyadmin.filters import BaseFilter
from ohmyadmin.forms import DateField, EmailField, Form, TextField
from ohmyadmin.layout import Card, FormElement, FormPlaceholder, Grid, Group, Layout
from ohmyadmin.resources import Resource
from ohmyadmin.tables import Column


class ByDateFilter(BaseFilter):
    class FilterForm(Form):
        before_date = DateField(label='Created from')
        after_date = DateField(label='Created until')

    def apply(self, request: Request, stmt: sa.sql.Select, form: FilterForm) -> sa.sql.Select:
        if form.before_date.data:
            stmt = stmt.where(Customer.created_at >= form.before_date.data)

        if form.after_date.data:
            stmt = stmt.where(Customer.created_at <= form.after_date.data)

        return stmt


class EditForm(Form):
    name = TextField(required=True)
    email = EmailField(required=True)
    phone = TextField()
    birthday = DateField()


class CustomerResource(Resource):
    icon = 'friends'
    entity_class = Customer
    form_class = EditForm
    filters = (ByDateFilter,)
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
