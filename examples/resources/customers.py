import sqlalchemy as sa
import wtforms
from markupsafe import Markup
from sqlalchemy.orm import selectinload
from starlette.requests import Request

import ohmyadmin.components.layout
from examples import icons
from examples.models import Comment, Customer, Order, OrderItem
from ohmyadmin import components, filters, formatters
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.components import BaseDisplayLayoutBuilder
from ohmyadmin.views.display import BuilderDisplayView
from ohmyadmin.views.table import TableView


class CustomerForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    email = wtforms.EmailField(validators=[wtforms.validators.data_required()])
    phone = wtforms.TelField()
    birthday = wtforms.DateField()


class DisplayLayout(BaseDisplayLayoutBuilder):
    def build(self, request: Request, model: Customer) -> components.Component:
        return ohmyadmin.components.layout.Grid(
            children=[
                ohmyadmin.components.layout.Column(
                    colspan=6,
                    children=[
                        components.DisplayFieldComponent(DisplayField("name"), model),
                        components.DisplayFieldComponent(
                            DisplayField(
                                "email",
                                formatter=formatters.LinkFormatter(
                                    url=lambda r, v: Markup(f"mailto:{v}"),
                                ),
                            ),
                            model,
                        ),
                        components.DisplayFieldComponent(
                            DisplayField(
                                "phone",
                                formatter=formatters.LinkFormatter(
                                    url=lambda r, v: Markup(f"tel:{v}"),
                                ),
                            ),
                            model,
                        ),
                        components.DisplayFieldComponent(
                            DisplayField("birthday", formatter=formatters.DateFormatter()),
                            model,
                        ),
                        components.Group(
                            label="Addresses",
                            children=[
                                ohmyadmin.components.layout.Grid(
                                    columns=4,
                                    children=[
                                        ohmyadmin.components.layout.Column(
                                            colspan=1,
                                            children=[
                                                components.DisplayValue(label="Country", value=address.country),
                                                components.DisplayValue(label="City", value=address.city),
                                                components.DisplayValue(label="ZIP", value=address.zip),
                                                components.DisplayValue(label="Street", value=address.street),
                                            ],
                                        ),
                                    ],
                                )
                                for address in model.addresses
                            ],
                        ),
                        components.Group(
                            label="Payments",
                            children=[
                                ohmyadmin.components.layout.Grid(
                                    children=[
                                        ohmyadmin.components.layout.Column(
                                            children=[
                                                components.DisplayValue(label="Reference", value=payment.reference),
                                                components.DisplayValue(
                                                    label="Amount",
                                                    value=payment.amount,
                                                    formatter=formatters.NumberFormatter(prefix="$"),
                                                ),
                                                components.DisplayValue(label="Currency", value=payment.currency_code),
                                                components.DisplayValue(label="Provider", value=payment.provider),
                                                components.DisplayValue(label="Method", value=payment.method),
                                                components.SeparatorComponent(),
                                            ]
                                        ),
                                    ]
                                )
                                for payment in model.payments
                            ],
                        ),
                        components.Group(
                            label="Orders",
                            children=[
                                ohmyadmin.components.layout.Grid(
                                    children=[
                                        ohmyadmin.components.layout.Column(
                                            children=[
                                                components.DisplayValue(label="Number", value=order.number),
                                                components.DisplayValue(label="Status", value=order.status),
                                                components.DisplayValue(
                                                    label="Items",
                                                    value=", ".join([str(item.product) for item in order.items]),
                                                ),
                                                components.DisplayValue(label="Total price", value=order.total_price),
                                                components.SeparatorComponent(),
                                            ]
                                        ),
                                    ]
                                )
                                for order in model.orders
                            ],
                        ),
                        components.Group(
                            label="Comments",
                            children=[
                                ohmyadmin.components.layout.Grid(
                                    children=[
                                        ohmyadmin.components.layout.Column(
                                            children=[
                                                components.DisplayValue(label="Title", value=comments.title),
                                                components.DisplayValue(label="Content", value=comments.content),
                                                components.DisplayValue(
                                                    label="Public",
                                                    value=comments.public,
                                                    formatter=formatters.BoolFormatter(),
                                                ),
                                                components.DisplayValue(label="Product", value=comments.product),
                                                components.DisplayValue(
                                                    label="Created at",
                                                    value=comments.created_at,
                                                    formatter=formatters.DateTimeFormatter(),
                                                ),
                                                components.SeparatorComponent(),
                                            ]
                                        ),
                                    ]
                                )
                                for comments in model.comments
                            ],
                        ),
                    ],
                ),
            ]
        )


class CustomerResource(ResourceScreen):
    icon = icons.ICON_FRIENDS
    group = "Shop"
    datasource = SADataSource(
        Customer,
        query_for_list=sa.select(Customer).order_by(Customer.name),
        query=(
            sa.select(Customer)
            .order_by(Customer.name)
            .options(
                selectinload(Customer.addresses),
                selectinload(Customer.comments).joinedload(Comment.product),
                selectinload(Customer.payments),
                selectinload(Customer.orders).selectinload(Order.items).joinedload(OrderItem.product),
            )
        ),
    )
    form_class = CustomerForm
    ordering_fields = "name", "email"
    searchable_fields = "name", "email", "phone"
    page_filters = [
        filters.DateFilter("created_at"),
        filters.DateFilter("birthday"),
    ]
    index_view = TableView(
        columns=[
            DisplayField("name", link=True),
            DisplayField("email"),
            DisplayField("phone"),
        ]
    )
    display_view = BuilderDisplayView(builder=DisplayLayout())
