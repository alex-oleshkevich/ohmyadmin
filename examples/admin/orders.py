import sqlalchemy as sa
import typing
import wtforms
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.models import Country, Currency, Customer, Order, OrderItem, Product
from ohmyadmin.components import display
from ohmyadmin.components.display import DisplayField
from ohmyadmin.components.layout import Card, Date, FormElement, FormText, Grid, Group, LayoutComponent
from ohmyadmin.ext.sqla import ChoiceFilter, DateRangeFilter, DecimalFilter, SQLAlchemyResource, choices_from
from ohmyadmin.filters import BaseFilter
from ohmyadmin.forms import (
    DecimalField,
    FieldList,
    Form,
    FormField,
    GridWidget,
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
    product_id = SelectField(validators=[wtforms.validators.data_required()], choices=choices_from(Product), coerce=int)
    quantity = IntegerField(validators=[wtforms.validators.data_required()])
    unit_price = DecimalField(validators=[wtforms.validators.data_required()])


class OrderResource(SQLAlchemyResource):
    icon = 'shopping-cart'
    entity_class = Order
    queryset = (
        sa.select(Order)
        # .join(Order.items)
        .options(
            # with_expression(Order.total_price, OrderItem.unit_price * OrderItem.quantity),
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
        yield StringField(name='number', validators=[wtforms.validators.data_required()])
        yield SelectField(
            name='customer_id',
            coerce=int,
            choices=choices_from(Customer),
            validators=[wtforms.validators.data_required()],
        )
        yield SelectField(name='status', choices=Order.Status.choices, validators=[wtforms.validators.data_required()])
        yield SelectField(
            name='currency_code',
            validators=[wtforms.validators.data_required()],
            choices=choices_from(Currency, value_column='code'),
        )
        yield SelectField(name='country_code', choices=choices_from(Country, value_column='code'))
        yield StringField(name='address')
        yield StringField(name='city')
        yield StringField(name='zip')
        yield MarkdownField(name='notes')
        yield FieldList(
            name='items',
            unbound_field=FormField(default=OrderItem, form_class=EditOrderItem, widget=GridWidget(columns=3)),
            default=[],
        )

    def get_form_layout(self, request: Request, form: Form, instance: Order) -> LayoutComponent:
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
                                FormElement(form.currency_code, colspan=3),
                                FormElement(form.country_code, colspan=2),
                                FormElement(form.city, colspan=2),
                                FormElement(form.zip, colspan=2),
                                FormElement(form.address, colspan='full'),
                                FormElement(form.notes, colspan='full'),
                            ],
                        ),
                        Card(
                            label='Order items',
                            children=[FormElement(form.items)],
                        ),
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
                        ),
                    ],
                ),
            ],
        )
