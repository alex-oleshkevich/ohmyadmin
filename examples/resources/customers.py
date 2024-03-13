import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from starlette_babel import formatters

from examples import icons
from examples.models import Address, Comment, Customer, Order, OrderItem
from ohmyadmin import components, filters
from ohmyadmin.components import CellAlign
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.resources.resource import ResourceScreen


class CustomerForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    email = wtforms.EmailField(validators=[wtforms.validators.data_required()])
    phone = wtforms.TelField()
    birthday = wtforms.DateField()


class CustomerDetailView(components.DetailView[Customer]):
    def compose(self, request: Request) -> components.Component:
        return components.Grid(
            children=[
                components.Column(
                    colspan=8,
                    children=[
                        components.ModelField("Name", components.Text(self.model.name)),
                        components.ModelField(
                            "Email",
                            components.Link(url=f"mailto:{self.model.email}", text=self.model.email),
                        ),
                        components.ModelField(
                            "Phone",
                            components.Link(url=f"tel:{self.model.phone}", text=self.model.phone),
                        ),
                        components.ModelField(
                            "Birthdate", components.Text(formatters.format_date(self.model.birthday))
                        ),
                        components.Group(
                            label="Addresses",
                            children=[
                                components.Table[Address](
                                    items=self.model.addresses,
                                    header=components.TableRow(
                                        children=[
                                            components.TableHeadCell("Country"),
                                            components.TableHeadCell("City"),
                                            components.TableHeadCell("ZIP"),
                                            components.TableHeadCell("Street"),
                                        ]
                                    ),
                                    row_builder=lambda row: components.TableRow(
                                        children=[
                                            components.TableColumn(components.Text(row.country)),
                                            components.TableColumn(components.Text(row.city)),
                                            components.TableColumn(components.Text(row.zip)),
                                            components.TableColumn(components.Text(row.street)),
                                        ]
                                    ),
                                ),
                            ],
                        ),
                        components.Group(
                            label="Payments",
                            children=[
                                components.Table(
                                    items=self.model.payments,
                                    header=components.TableRow(
                                        children=[
                                            components.TableHeadCell("Reference"),
                                            components.TableHeadCell("Currency"),
                                            components.TableHeadCell("Provider"),
                                            components.TableHeadCell("Method"),
                                            components.TableHeadCell("Amount"),
                                        ]
                                    ),
                                    row_builder=lambda row: components.TableRow(
                                        children=[
                                            components.TableColumn(components.Text(row.reference)),
                                            components.TableColumn(components.Text(row.currency_code)),
                                            components.TableColumn(components.Text(row.provider)),
                                            components.TableColumn(components.Text(row.method)),
                                            components.TableColumn(
                                                components.Text(formatters.format_currency(row.amount, "USD")),
                                                align=CellAlign.RIGHT,
                                            ),
                                        ]
                                    ),
                                ),
                            ],
                        ),
                        components.Group(
                            label="Orders",
                            children=[
                                components.Table(
                                    items=self.model.orders,
                                    header=components.TableRow(
                                        children=[
                                            components.TableHeadCell("Number"),
                                            components.TableHeadCell("Status"),
                                            components.TableHeadCell("Items"),
                                            components.TableHeadCell("Total price"),
                                        ]
                                    ),
                                    row_builder=lambda row: components.TableRow(
                                        children=[
                                            components.TableColumn(components.Text(row.number)),
                                            components.TableColumn(components.Text(row.status)),
                                            components.TableColumn(
                                                components.Text(", ".join([str(item.product) for item in row.items]))
                                            ),
                                            components.TableColumn(
                                                components.Text(formatters.format_currency(row.total_price, "USD"))
                                            ),
                                        ]
                                    ),
                                ),
                            ],
                        ),
                        components.Group(
                            label="Comments",
                            children=[
                                components.Table(
                                    items=self.model.comments,
                                    header=components.TableRow(
                                        children=[
                                            components.TableHeadCell("Title"),
                                            components.TableHeadCell("Content"),
                                            components.TableHeadCell("Product"),
                                            components.TableHeadCell("Public"),
                                            components.TableHeadCell("Created at"),
                                        ]
                                    ),
                                    row_builder=lambda row: components.TableRow(
                                        children=[
                                            components.TableColumn(components.Text(row.title)),
                                            components.TableColumn(components.Text(row.content)),
                                            components.TableColumn(components.Text(row.product)),
                                            components.TableColumn(
                                                components.BoolValue(row.public),
                                            ),
                                            components.TableColumn(
                                                components.Text(formatters.format_datetime(row.created_at))
                                            ),
                                        ]
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        )


class CustomerFormView(components.FormView[CustomerForm, Customer]):
    def compose(self, request: Request) -> components.Component:
        return components.Grid(
            children=[
                components.Column(
                    colspan=5,
                    children=[
                        components.FormInput(self.form.name),
                        components.FormInput(self.form.email),
                        components.Grid(
                            columns=2,
                            children=[
                                components.FormInput(self.form.phone),
                                components.FormInput(self.form.birthday),
                            ],
                        ),
                    ],
                ),
            ]
        )


class CustomerIndexView(components.IndexView[Customer]):
    def compose(self, request: Request) -> components.Component:
        return components.Table(
            items=self.models,
            header=components.TableRow(
                children=[
                    components.TableSortableHeadCell("Name", sort_field="name"),
                    components.TableSortableHeadCell("Email", sort_field="email"),
                    components.TableHeadCell("Phone"),
                ]
            ),
            row_builder=lambda row: components.TableRow(
                children=[
                    components.TableColumn(
                        components.Link(text=row.name, url=CustomerResource.get_edit_page_route(row.id))
                    ),
                    components.TableColumn(components.Link(text=row.email, url=f"mailto:{row.email}")),
                    components.TableColumn(components.Link(text=row.phone, url=f"tel:{row.phone}")),
                ]
            ),
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
    index_view_class = CustomerIndexView
    form_view_class = CustomerFormView
    detail_view_class = CustomerDetailView
