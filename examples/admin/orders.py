import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import joinedload, selectinload, with_expression
from starlette.requests import Request

from examples.models import Order, OrderItem
from ohmyadmin import filters, formatters
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.metrics import PartitionMetric, PartitionResult, TrendMetric, TrendResult, ValueMetric
from ohmyadmin.resources import Resource
from ohmyadmin.views.table import TableColumn

STATUS_COLORS: dict[str, str] = {
    Order.Status.NEW: 'rgb(59 130 246)',
    Order.Status.SHIPPED: 'rgb(99 102 241)',
    Order.Status.PROCESSING: 'rgb(234 179 8)',
    Order.Status.DELIVERED: 'rgb(34 197 94)',
    Order.Status.CANCELLED: 'rgb(239 68 68)',
}


class OrderItemForm(wtforms.Form):
    product_id = wtforms.SelectField(validators=[wtforms.validators.data_required()], coerce=int)
    quantity = wtforms.IntegerField(validators=[wtforms.validators.data_required()])
    unit_price = wtforms.DecimalField(validators=[wtforms.validators.data_required()])


class OrderForm(wtforms.Form):
    number = wtforms.StringField(validators=[wtforms.validators.data_required()])
    customer_id = wtforms.SelectField(coerce=int, validators=[wtforms.validators.data_required()])
    status = wtforms.SelectField(choices=Order.Status.choices, validators=[wtforms.validators.data_required()])
    currency_code = wtforms.SelectField(validators=[wtforms.validators.data_required()])
    country_code = wtforms.SelectField(validators=[wtforms.validators.data_required()])
    address = wtforms.SelectField()
    city = wtforms.SelectField()
    zip = wtforms.SelectField()
    notes = wtforms.TextAreaField()
    items = wtforms.FieldList(wtforms.FormField(OrderItemForm, default=OrderItem), default=[], min_entries=1)


class ByStatusMetric(PartitionMetric):
    label = 'By status'

    async def calculate(self, request: Request) -> PartitionResult:
        stmt = sa.select(
            sa.func.count().label('total'),
            Order.status,
        ).group_by(sa.text('2'))
        result = await request.state.dbsession.execute(stmt)
        return PartitionResult(
            {
                row.status: {
                    'color': STATUS_COLORS[row.status],
                    'value': row.total,
                }
                for row in result.all()
            }
        )


class TotalProductsMetric(ValueMetric):
    suffix = 'orders'

    async def calculate(self, request: Request) -> str:
        stmt = sa.select(sa.func.count()).select_from(sa.select(Order).subquery())
        return await request.state.dbsession.scalar(stmt)


class OrdersByYear(TrendMetric):
    label = 'Orders by year'

    async def calculate(self, request: Request) -> TrendResult:
        stmt = (
            sa.select(
                sa.func.date_trunc('year', Order.created_at).label('year'),
                sa.func.count().label('total'),
            )
            .order_by(sa.text('1'))
            .group_by(sa.text('1'))
        )
        result = await request.state.dbsession.execute(stmt)
        return TrendResult(
            current_value=42,
            series=[(row.year.year, row.total) for row in result.all()],
        )


class Orders(Resource):
    icon = 'shopping-cart'
    form_class = OrderForm
    metrics = [TotalProductsMetric, ByStatusMetric, OrdersByYear]
    datasource = SQLADataSource(
        Order,
        query=sa.select(Order).options(
            joinedload(Order.customer),
            joinedload(Order.currency),
            selectinload(Order.items),
        ),
        query_for_list=(
            sa.select(Order)
            .join(Order.items)
            .options(
                with_expression(Order.total_price, OrderItem.unit_price + OrderItem.quantity),
                joinedload(Order.customer),
                joinedload(Order.currency),
            )
        ),
    )
    filters = [
        filters.ChoiceFilter('status', choices=Order.Status.choices),
        # filters.ChoiceFilter(Order.currency_code),
        filters.DecimalFilter('total_price'),
        filters.DateRangeFilter('created_at'),
    ]
    columns = [
        TableColumn('number', searchable=True, link=True),
        TableColumn('customer'),
        TableColumn(
            'status',
            sortable=True,
            formatter=formatters.BadgeFormatter(
                color_map={
                    Order.Status.NEW: 'blue',
                    Order.Status.SHIPPED: 'green',
                    Order.Status.PROCESSING: 'yellow',
                    Order.Status.DELIVERED: 'green',
                    Order.Status.CANCELLED: 'red',
                }
            ),
        ),
        TableColumn('currency'),
        TableColumn('total_price', formatter=formatters.NumberFormatter(suffix='USD')),
        TableColumn('created_at', label='Order date', formatter=formatters.DateFormatter()),
    ]
