import sqlalchemy as sa
import wtforms
from markupsafe import Markup
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from examples import icons
from examples.models import Comment, Customer, Order, OrderItem
from ohmyadmin import components, filters, formatters
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.components import BaseDisplayLayoutBuilder
from ohmyadmin.views.table import TableView


class CustomerForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    email = wtforms.EmailField(validators=[wtforms.validators.data_required()])
    phone = wtforms.TelField()
    birthday = wtforms.DateField()


class DisplayLayout(BaseDisplayLayoutBuilder):
    def build(self, request: Request, model: Customer) -> components.Component:
        return components.GridComponent(
            children=[
                components.ColumnComponent(
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
                        components.GroupComponent(
                            label="Addresses",
                            children=[
                                components.GridComponent(
                                    columns=4,
                                    children=[
                                        components.ColumnComponent(
                                            colspan=1,
                                            children=[
                                                components.DisplayValueComponent(
                                                    label="Country", value=address.country
                                                ),
                                                components.DisplayValueComponent(label="City", value=address.city),
                                                components.DisplayValueComponent(label="ZIP", value=address.zip),
                                                components.DisplayValueComponent(label="Street", value=address.street),
                                            ],
                                        ),
                                    ],
                                )
                                for address in model.addresses
                            ],
                        ),
                        components.GroupComponent(
                            label="Payments",
                            children=[
                                components.GridComponent(
                                    children=[
                                        components.ColumnComponent(
                                            children=[
                                                components.DisplayValueComponent(
                                                    label="Reference", value=payment.reference
                                                ),
                                                components.DisplayValueComponent(
                                                    label="Amount",
                                                    value=payment.amount,
                                                    formatter=formatters.NumberFormatter(prefix="$"),
                                                ),
                                                components.DisplayValueComponent(
                                                    label="Currency", value=payment.currency_code
                                                ),
                                                components.DisplayValueComponent(
                                                    label="Provider", value=payment.provider
                                                ),
                                                components.DisplayValueComponent(label="Method", value=payment.method),
                                                components.SeparatorComponent(),
                                            ]
                                        ),
                                    ]
                                )
                                for payment in model.payments
                            ],
                        ),
                        components.GroupComponent(
                            label="Orders",
                            children=[
                                components.GridComponent(
                                    children=[
                                        components.ColumnComponent(
                                            children=[
                                                components.DisplayValueComponent(label="Number", value=order.number),
                                                components.DisplayValueComponent(label="Status", value=order.status),
                                                components.DisplayValueComponent(
                                                    label="Items",
                                                    value=", ".join([str(item.product) for item in order.items]),
                                                ),
                                                components.DisplayValueComponent(
                                                    label="Total price", value=order.total_price
                                                ),
                                                components.SeparatorComponent(),
                                            ]
                                        ),
                                    ]
                                )
                                for order in model.orders
                            ],
                        ),
                        components.GroupComponent(
                            label="Comments",
                            children=[
                                components.GridComponent(
                                    children=[
                                        components.ColumnComponent(
                                            children=[
                                                components.DisplayValueComponent(label="Title", value=comments.title),
                                                components.DisplayValueComponent(
                                                    label="Content", value=comments.content
                                                ),
                                                components.DisplayValueComponent(
                                                    label="Public",
                                                    value=comments.public,
                                                    formatter=formatters.BoolFormatter(),
                                                ),
                                                components.DisplayValueComponent(
                                                    label="Product", value=comments.product
                                                ),
                                                components.DisplayValueComponent(
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
    display_layout_class = DisplayLayout
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
