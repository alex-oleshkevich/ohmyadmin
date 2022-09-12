import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload, with_expression
from starlette.requests import Request

from examples.models import Country, Currency, Customer, Order, OrderItem
from ohmyadmin.forms import (
    Card,
    Form,
    FormField,
    FormPlaceholder,
    Grid,
    Group,
    Layout,
    MarkdownField,
    SelectField,
    TextField,
    choices_from,
)
from ohmyadmin.metrics import CountMetric
from ohmyadmin.resources import Resource
from ohmyadmin.tables import BadgeColumn, Column, DateColumn, NumberColumn


class TotalOrders(CountMetric):
    label = 'Orders'

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(sa.select(Order))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class OpenOrders(CountMetric):
    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(sa.select(Order).where(Order.status == 'New'))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class AveragePrice(CountMetric):
    value_prefix = 'USD'
    round = 2

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.avg(OrderItem.unit_price * OrderItem.quantity)).join(Order.items)
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class OrderResource(Resource):
    icon = 'shopping-cart'
    entity_class = Order
    queryset = (
        sa.select(Order)
        .join(Order.items)
        .options(
            with_expression(Order.total_price, OrderItem.unit_price * OrderItem.quantity),
            joinedload(Order.customer),
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
    form_fields = [
        TextField('number', required=True),
        SelectField('customer_id', required=True, coerce=int, choices=choices_from(Customer)),
        TextField('status', required=True),
        SelectField('currency', required=True, choices=choices_from(Currency, value_column='code')),
        SelectField('country', choices=choices_from(Country, value_column='code')),
        TextField('address'),
        TextField('city'),
        TextField('zip'),
        TextField('notes'),
        MarkdownField('notes'),
        # EmbedManyField('items', form_class=Form.from_fields([
        #     SelectField('product_id', required=True, choices=choices_from(Product)),
        #     IntegerField('quantity', required=True),
        #     DecimalField('unit_price', required=True),
        # ])),
    ]

    def get_form_layout(self, request: Request, form: Form[Order]) -> Layout:
        return Grid(
            cols=3,
            children=[
                Group(
                    colspan=2,
                    children=[
                        Card(
                            columns=6,
                            children=[
                                FormField(form.number, colspan=3),
                                FormField(form.customer_id, colspan=3),
                                FormField(form.status, colspan=3),
                                FormField(form.currency, colspan=3),
                                FormField(form.country, colspan=3),
                                FormField(form.address, colspan='full'),
                                FormField(form.city, colspan=2),
                                FormField(form.zip, colspan=2),
                                FormField(form.notes, colspan='full'),
                            ],
                        ),
                        Card(
                            children=[
                                # FormField(form.items),
                            ]
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
                                            if form.instance.created_at
                                            else '-'
                                        ),
                                    ),
                                    FormPlaceholder(
                                        'Updated at',
                                        (
                                            form.instance.updated_at.date().isoformat()
                                            if form.instance.updated_at
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
