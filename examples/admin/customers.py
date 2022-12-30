from __future__ import annotations

import typing
import wtforms
from starlette.requests import Request

from examples.models import Customer
from ohmyadmin.display import DisplayField
from ohmyadmin.ext.sqla import DateFilter, SQLAlchemyResource
from ohmyadmin.filters import BaseFilter
from ohmyadmin.forms import AsyncForm
from ohmyadmin.layout import Card, Date, FormElement, FormText, Grid, Group, LayoutComponent


class CustomerResource(SQLAlchemyResource):
    icon = 'friends'
    entity_class = Customer

    def get_filters(self, request: Request) -> typing.Iterable[BaseFilter]:
        yield DateFilter(Customer.created_at)
        yield DateFilter(Customer.birthday)

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        yield DisplayField('name', sortable=True, link=True, searchable=True)
        yield DisplayField('email', sortable=True, searchable=True)
        yield DisplayField('phone', searchable=True)

    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        yield wtforms.StringField(name='name', validators=[wtforms.validators.data_required()])
        yield wtforms.EmailField(name='email', validators=[wtforms.validators.data_required()])
        yield wtforms.StringField(name='phone')
        yield wtforms.DateField(name='birthday')

    def get_form_layout(self, request: Request, form: AsyncForm, instance: Customer) -> LayoutComponent:
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
                                FormText('Created at', Date(instance.created_at)),
                                FormText('Updated at', Date(instance.updated_at)),
                            ]
                        )
                    ],
                ),
            ],
        )
