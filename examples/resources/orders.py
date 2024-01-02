import decimal

import wtforms
import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload, with_expression
from starlette.requests import Request

from examples import icons
from examples.models import Country, Currency, Customer, Order, OrderItem, Product
from ohmyadmin import components, filters, formatters
from ohmyadmin.datasources.sqlalchemy import load_choices, SADataSource
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.forms.utils import safe_int_coerce
from ohmyadmin.metrics import Partition, PartitionMetric, TrendMetric, TrendValue, ValueMetric, ValueValue
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.components import BaseDisplayLayoutBuilder
from ohmyadmin.views.table import TableView

STATUS_COLORS: dict[str, str] = {
    Order.Status.NEW: "rgb(59 130 246)",
    Order.Status.SHIPPED: "rgb(99 102 241)",
    Order.Status.PROCESSING: "rgb(234 179 8)",
    Order.Status.DELIVERED: "rgb(34 197 94)",
    Order.Status.CANCELLED: "rgb(239 68 68)",
}


class OrderItemForm(wtforms.Form):
    product_id = wtforms.SelectField(validators=[wtforms.validators.data_required()], coerce=safe_int_coerce)
    quantity = wtforms.IntegerField(validators=[wtforms.validators.data_required()])
    unit_price = wtforms.DecimalField(validators=[wtforms.validators.data_required()])


class OrderForm(wtforms.Form):
    number = wtforms.StringField(validators=[wtforms.validators.data_required()])
    customer_id = wtforms.SelectField(coerce=safe_int_coerce, validators=[wtforms.validators.data_required()])
    status = wtforms.SelectField(choices=Order.Status.choices, validators=[wtforms.validators.data_required()])
    currency_code = wtforms.SelectField(validators=[wtforms.validators.data_required()])
    country_code = wtforms.SelectField(validators=[wtforms.validators.data_required()])
    address = wtforms.StringField()
    city = wtforms.StringField()
    zip = wtforms.StringField()
    notes = wtforms.TextAreaField()
    items = wtforms.FieldList(wtforms.FormField(OrderItemForm, default=OrderItem), default=[], min_entries=1)


class ByStatusMetric(PartitionMetric):
    label = "By status"

    async def calculate(self, request: Request) -> list[Partition]:
        stmt = sa.select(
            sa.func.count().label("total"),
            Order.status,
        ).group_by(sa.text("2"))
        result = await request.state.dbsession.execute(stmt)
        return [Partition(label=row.status, value=row.total, color=STATUS_COLORS[row.status]) for row in result.all()]


class TotalProductsMetric(ValueMetric):
    suffix = "orders"

    async def calculate(self, request: Request) -> ValueValue:
        stmt = sa.select(sa.func.count()).select_from(sa.select(Order).subquery())
        return await request.state.dbsession.scalar(stmt)


class OrdersByYear(TrendMetric):
    label = "Orders by year"
    show_current_value = True
    formatter = formatters.StringFormatter(suffix=" orders this month")

    async def calculate_current_value(self, request: Request) -> int | float | decimal.Decimal:
        stmt = sa.select(sa.func.count("*")).where(Order.created_at >= sa.func.now() - sa.text("interval '30 day'"))
        return await request.state.dbsession.scalar(stmt)

    async def calculate(self, request: Request) -> list[TrendValue]:
        stmt = (
            sa.select(
                sa.func.date_trunc("year", Order.created_at).label("year"),
                sa.func.count().label("total"),
            )
            .order_by(sa.text("1"))
            .group_by(sa.text("1"))
        )
        result = await request.state.dbsession.execute(stmt)
        return [TrendValue(label=row.year.year, value=row.total) for row in result.all()]


class DisplayLayout(BaseDisplayLayoutBuilder):
    def build(self, request: Request, model: Customer) -> components.Component:
        return components.GridComponent()


class OrdersResource(ResourceScreen):
    group = "Shop"
    icon = icons.ICON_ORDER
    form_class = OrderForm
    page_metrics = [TotalProductsMetric(), ByStatusMetric(), OrdersByYear()]
    datasource = SADataSource(
        Order,
        query=sa.select(Order).options(
            joinedload(Order.customer),
            joinedload(Order.currency),
            joinedload(Order.country),
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
    page_filters = [
        filters.ChoiceFilter("status", choices=Order.Status.choices),
        # filters.ChoiceFilter(Order.currency_code),
        filters.DecimalFilter("total_price"),
        filters.DateRangeFilter("created_at"),
    ]
    searchable_fields = ("number",)
    ordering_fields = ("status",)
    display_fields = [
        DisplayField(
            "status",
            formatter=formatters.BadgeFormatter(
                color_map={
                    Order.Status.NEW: "blue",
                    Order.Status.SHIPPED: "green",
                    Order.Status.PROCESSING: "yellow",
                    Order.Status.DELIVERED: "green",
                    Order.Status.CANCELLED: "red",
                }
            ),
        ),
        DisplayField("currency"),
        DisplayField("total_price", formatter=formatters.NumberFormatter(suffix="USD")),
        DisplayField("created_at", label="Order date", formatter=formatters.DateFormatter()),
        DisplayField("updated_at", label="Update date", formatter=formatters.DateFormatter()),
        DisplayField("address"),
        DisplayField("city"),
        DisplayField("zip"),
        DisplayField("notes"),
        DisplayField("currency"),
        DisplayField("country"),
    ]
    index_view = TableView(
        columns=[
            DisplayField("number", link=True),
            DisplayField("customer"),
            DisplayField(
                "status",
                formatter=formatters.BadgeFormatter(
                    color_map={
                        Order.Status.NEW: "blue",
                        Order.Status.SHIPPED: "green",
                        Order.Status.PROCESSING: "yellow",
                        Order.Status.DELIVERED: "green",
                        Order.Status.CANCELLED: "red",
                    }
                ),
            ),
            DisplayField("currency"),
            DisplayField("total_price", formatter=formatters.NumberFormatter(suffix="USD")),
            DisplayField("created_at", label="Order date", formatter=formatters.DateFormatter()),
        ]
    )

    async def init_form(self, request: Request, form: OrderForm) -> None:
        await load_choices(request.state.dbsession, form.customer_id, sa.select(Customer))
        await load_choices(request.state.dbsession, form.currency_code, sa.select(Currency), value_attr="code")
        await load_choices(request.state.dbsession, form.country_code, sa.select(Country), value_attr="code")

        for item_form in form.items:
            await load_choices(request.state.dbsession, item_form.product_id, sa.select(Product))
