import decimal

import wtforms
import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload, with_expression
from starlette.requests import Request

import ohmyadmin.components.table
from examples import icons
from examples.models import Country, Currency, Customer, Order, OrderItem, Product
from examples.resources.customers import CustomerResource
from ohmyadmin import components, filters, formatters
from ohmyadmin.datasources.sqlalchemy import load_choices, SADataSource
from ohmyadmin.forms.utils import safe_int_coerce
from ohmyadmin.metrics import Partition, PartitionMetric, TrendMetric, TrendValue, ValueMetric, ValueValue
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.components import BadgeColor

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
    formatter = formatters.String(suffix=" orders this month")

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


class OrderDetailView(components.DetailView[Order]):
    def build(self, request: Request) -> components.Component:
        return components.Grid(
            children=[
                components.Column(
                    colspan=8,
                    children=[
                        components.ModelField(
                            "Customer",
                            self.model.customer,
                            value_builder=lambda _: components.Link(
                                text=self.model.customer,
                                url=CustomerResource.get_display_page_route(self.model.customer_id),
                            ),
                        ),
                        components.ModelField(
                            "Status",
                            self.model.status,
                            value_builder=lambda value: components.Badge(
                                value,
                                {
                                    Order.Status.NEW: BadgeColor.BLUE,
                                    Order.Status.SHIPPED: BadgeColor.GREEN,
                                    Order.Status.PROCESSING: BadgeColor.YELLOW,
                                    Order.Status.DELIVERED: BadgeColor.GREEN,
                                    Order.Status.CANCELLED: BadgeColor.RED,
                                },
                            ),
                        ),
                        components.ModelField(
                            "Total price",
                            sum([item.unit_price * item.quantity for item in self.model.items]),
                            formatter=formatters.Number(prefix="USD "),
                        ),
                        components.ModelField("Order date", self.model.created_at),
                        components.ModelField("Update date", self.model.updated_at),
                        components.ModelField("Address", self.model.address),
                        components.ModelField("City", self.model.city),
                        components.ModelField("ZIP", self.model.zip),
                        components.ModelField("Currency", self.model.currency),
                        components.ModelField("Country", self.model.country),
                        components.ModelField("Notes", self.model.notes),
                        components.Group(
                            label="Ordered products",
                            children=[
                                ohmyadmin.components.table.Table(
                                    items=self.model.items,
                                    headers=["Product", "Quantity", "Price"],
                                    row_builder=lambda row: [
                                        ohmyadmin.components.table.TableColumn(row.product),
                                        ohmyadmin.components.table.TableColumn(row.quantity, align="right"),
                                        ohmyadmin.components.table.TableColumn(
                                            row.unit_price * row.quantity, align="right", formatter=formatters.Number()
                                        ),
                                    ],
                                    summary=[
                                        ohmyadmin.components.table.TableColumn(value="Total", align="right", colspan=2),
                                        ohmyadmin.components.table.TableColumn(
                                            align="right",
                                            formatter=formatters.Number(prefix="USD "),
                                            value=sum([item.unit_price * item.quantity for item in self.model.items]),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        )


class OrderFormView(components.FormView[OrderForm, Order]):
    def build(self, request: Request) -> components.Component:
        return components.Grid(
            children=[
                components.Column(
                    colspan=8,
                    children=[
                        components.FormInput(self.form.customer_id),
                        components.Grid(
                            columns=3,
                            children=[
                                components.FormInput(self.form.number),
                                components.FormInput(self.form.status),
                                components.FormInput(self.form.currency_code),
                            ],
                        ),
                        components.FormInput(self.form.notes),
                        components.Group(
                            label="Order items",
                            children=[
                                components.RepeatedFormInput(
                                    self.form.items,
                                    builder=lambda field: components.Grid(
                                        columns=3, children=[components.FormInput(subfield) for subfield in field]
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
                components.Column(
                    colspan=4,
                    children=[
                        components.Group(
                            children=[
                                components.Grid(
                                    columns=2,
                                    children=[
                                        components.FormInput(self.form.country_code),
                                        components.FormInput(self.form.city),
                                    ],
                                ),
                                components.Grid(
                                    columns=2,
                                    children=[
                                        components.FormInput(self.form.address),
                                        components.FormInput(self.form.zip),
                                    ],
                                ),
                            ]
                        ),
                    ],
                ),
            ]
        )


class OrderIndexView(components.IndexView[Order]):
    def build(self, request: Request) -> components.Component:
        return components.Table(
            items=self.models,
            header=components.TableRow(
                children=[
                    components.TableHeadCell("Number"),
                    components.TableHeadCell("Customer"),
                    components.TableSortableHeadCell("Status", sort_field="status"),
                    components.TableHeadCell("Currency"),
                    components.TableHeadCell("Total price"),
                    components.TableHeadCell("Order date"),
                ]
            ),
            row_builder=lambda row: components.TableRow(
                children=[
                    components.TableColumn(
                        value_builder=lambda: components.Link(
                            text=row.number,
                            url=OrdersResource.get_edit_page_route(row.id),
                        )
                    ),
                    components.TableColumn(
                        value_builder=lambda: components.Link(
                            text=str(row.customer), url=CustomerResource.get_display_page_route(row.customer_id)
                        )
                    ),
                    components.TableColumn(
                        value_builder=lambda: components.Badge(
                            row.status,
                            colors={
                                Order.Status.NEW: BadgeColor.BLUE,
                                Order.Status.SHIPPED: BadgeColor.GREEN,
                                Order.Status.PROCESSING: BadgeColor.YELLOW,
                                Order.Status.DELIVERED: BadgeColor.INDIGO,
                                Order.Status.CANCELLED: BadgeColor.RED,
                            },
                        )
                    ),
                    components.TableColumn(str(row.currency)),
                    components.TableColumn(row.total_price, formatter=formatters.Number(prefix="$ ")),
                    components.TableColumn(row.created_at),
                ]
            ),
        )


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
            selectinload(Order.items).joinedload(OrderItem.product),
        ),
        query_for_list=(
            sa.select(Order)
            .distinct()
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
    index_view_class = OrderIndexView
    detail_view_class = OrderDetailView
    form_view_class = OrderFormView

    async def init_form(self, request: Request, form: OrderForm) -> None:
        await load_choices(request.state.dbsession, form.customer_id, sa.select(Customer))
        await load_choices(request.state.dbsession, form.currency_code, sa.select(Currency), value_attr="code")
        await load_choices(request.state.dbsession, form.country_code, sa.select(Country), value_attr="code")

        for item_form in form.items:
            await load_choices(request.state.dbsession, item_form.product_id, sa.select(Product))
