import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload, with_expression
from starlette.requests import Request

from examples.models import Country, Currency, Customer, Order, OrderItem, Product
from ohmyadmin.components import Card, Component, FormElement, FormPlaceholder, FormRepeater, Grid, Group
from ohmyadmin.ext.sqla import choices_from
from ohmyadmin.forms import (
    DecimalField,
    FieldList,
    Form,
    FormField,
    IntegerField,
    MarkdownField,
    SelectField,
    StringField,
)
from ohmyadmin.metrics import ValueMetric
from ohmyadmin.resources import Resource
from ohmyadmin.tables import BadgeColumn, Column, DateColumn, NumberColumn


class TotalOrders(ValueMetric):
    label = 'Orders'

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(sa.select(Order))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class OpenOrders(ValueMetric):
    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(sa.select(Order).where(Order.status == 'New'))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class AveragePrice(ValueMetric):
    value_prefix = 'USD'
    round = 2

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.avg(OrderItem.unit_price * OrderItem.quantity)).join(Order.items)
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class EditOrderItem(Form):
    product_id = SelectField(required=True, choices=choices_from(Product), coerce=int)
    quantity = IntegerField(required=True)
    unit_price = DecimalField(required=True)


class EditForm(Form):
    number = StringField(required=True)
    customer_id = SelectField(required=True, coerce=int, choices=choices_from(Customer))
    status = StringField(required=True)
    currency = SelectField(required=True, choices=choices_from(Currency, value_column='code'))
    country = SelectField(choices=choices_from(Country, value_column='code'))
    address = StringField()
    city = StringField()
    zip = StringField()
    notes = MarkdownField()
    items = FieldList(FormField(default=OrderItem, form_class=EditOrderItem), default=[])


class OrderResource(Resource):
    icon = 'shopping-cart'
    entity_class = Order
    form_class = EditForm
    queryset = (
        sa.select(Order)
        .join(Order.items)
        .options(
            with_expression(Order.total_price, OrderItem.unit_price * OrderItem.quantity),
            joinedload(Order.customer),
            joinedload(Order.currency),
            selectinload(Order.items),
        )
    )
    metrics = [
        TotalOrders(),
        OpenOrders(),
        AveragePrice(),
    ]
    table_columns = [
        Column('number', searchable=True, link=True),
        Column('customer'),
        BadgeColumn(
            'status',
            sortable=True,
            colors={
                Order.Status.NEW: 'blue',
                Order.Status.SHIPPED: 'green',
                Order.Status.PROCESSING: 'yellow',
                Order.Status.DELIVERED: 'green',
                Order.Status.CANCELLED: 'red',
            },
        ),
        Column('currency'),
        NumberColumn('total_price'),
        DateColumn('created_at', label='Order date'),
    ]

    def get_form_layout(self, request: Request, form: Form) -> Component:
        return Grid(
            columns=3,
            children=[
                Group(
                    colspan=2,
                    children=[
                        Card(
                            columns=6,
                            children=[
                                FormElement(form.number, colspan=3),
                                FormElement(form.customer_id, colspan=3),
                                FormElement(form.status, colspan=3),
                                FormElement(form.currency, colspan=3),
                                FormElement(form.country, colspan=3),
                                FormElement(form.address, colspan='full'),
                                FormElement(form.city, colspan=2),
                                FormElement(form.zip, colspan=2),
                                FormElement(form.notes, colspan='full'),
                            ],
                        ),
                        Card(
                            title='Order items',
                            children=[
                                FormRepeater(
                                    form.items,
                                    layout_builder=lambda f: Grid(
                                        columns=3,
                                        children=[
                                            FormElement(f.product_id),
                                            FormElement(f.quantity),
                                            FormElement(f.unit_price),
                                        ],
                                    ),
                                )
                            ],
                        ),
                    ],
                ),
                Group(
                    colspan=1,
                    children=Card(
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
                            ),
                        ]
                    ),
                ),
            ],
        )
