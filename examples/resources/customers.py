import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from examples import icons
from examples.models import Address, Comment, Customer, Order, OrderItem
from ohmyadmin import components, filters, formatters
from ohmyadmin.components import CellAlign
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.resources.resource import ResourceScreen


class CustomerForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    email = wtforms.EmailField(validators=[wtforms.validators.data_required()])
    phone = wtforms.TelField()
    birthday = wtforms.DateField()


class CustomerDetailView(components.DetailView[Customer]):
    def build(self, request: Request) -> components.Component:
        return components.Grid(
            children=[
                components.Column(
                    colspan=8,
                    children=[
                        components.ModelField("Name", components.Text(self.model.name)),
                        components.ModelField(
                            "Email",
                            components.Text(
                                self.model.email,
                                formatter=formatters.Link(self.model.email, protocol="mailto"),
                            ),
                        ),
                        components.ModelField(
                            "Phone",
                            components.Text(
                                self.model.phone,
                                formatter=formatters.Link(self.model.phone, protocol="tel"),
                            ),
                        ),
                        components.ModelField(
                            "Birthdate", components.Text(self.model.birthday, formatter=formatters.Date())
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
                                                components.Text(row.amount, formatter=formatters.Number(prefix="$ ")),
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
                                                components.Text(
                                                    row.total_price, formatter=formatters.Number(prefix="$ ")
                                                )
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
                                                components.Text(row.created_at, formatter=formatters.DateTime())
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
    def build(self, request: Request) -> components.Component:
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
    def build(self, request: Request) -> components.Component:
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
                    components.TableColumn(components.Text(row.email, formatter=formatters.Link(protocol="mailto"))),
                    components.TableColumn(components.Text(row.phone, formatter=formatters.Link(protocol="tel"))),
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
