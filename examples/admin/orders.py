import sqlalchemy as sa
import typing
import wtforms
from sqlalchemy.orm import joinedload, selectinload, with_expression
from starlette.requests import Request

from examples.models import Country, Currency, Customer, Order, OrderItem, Product
from ohmyadmin.components import Card, Component, FormElement, FormPlaceholder, FormRepeater, Grid, Group, display
from ohmyadmin.components.display import DisplayField
from ohmyadmin.ext.sqla import ChoiceFilter, DateRangeFilter, DecimalFilter, SQLAlchemyResource, choices_from
from ohmyadmin.filters import BaseFilter
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
from ohmyadmin.metrics import Metric, ValueMetric


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


class OrderResource(SQLAlchemyResource):
    icon = 'shopping-cart'
    entity_class = Order
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

    def get_filters(self, request: Request) -> typing.Iterable[BaseFilter]:
        yield ChoiceFilter(Order.status, choices=Order.Status.choices)
        yield ChoiceFilter(Order.currency_code, choices=choices_from(Currency, value_column='code'))
        yield DecimalFilter(Order.total_price)
        yield DateRangeFilter(Order.created_at)

    def get_metrics(self, request: Request) -> typing.Iterable[Metric]:
        yield TotalOrders()
        yield OpenOrders()
        yield AveragePrice()

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        yield DisplayField('number', searchable=True, link=True)
        yield DisplayField('customer')
        yield DisplayField(
            'status',
            sortable=True,
            component=display.Badge(
                {
                    Order.Status.NEW: 'blue',
                    Order.Status.SHIPPED: 'green',
                    Order.Status.PROCESSING: 'yellow',
                    Order.Status.DELIVERED: 'green',
                    Order.Status.CANCELLED: 'red',
                }
            ),
        )
        yield DisplayField('currency')
        yield DisplayField('total_price', component=display.Money('USD'))
        yield DisplayField('created_at', label='Order date', component=display.DateTime())

    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        yield StringField(name='number', required=True)
        yield SelectField(name='customer_id', required=True, coerce=int, choices=choices_from(Customer))
        yield StringField(name='status', required=True)
        yield SelectField(name='currency', required=True, choices=choices_from(Currency, value_column='code'))
        yield SelectField(name='country', choices=choices_from(Country, value_column='code'))
        yield StringField(name='address')
        yield StringField(name='city')
        yield StringField(name='zip')
        yield MarkdownField(name='notes')
        yield FieldList(name='items', unbound_field=FormField(default=OrderItem, form_class=EditOrderItem), default=[])

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
