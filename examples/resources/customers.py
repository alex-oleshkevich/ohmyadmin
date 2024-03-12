import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import selectinload
from starlette.requests import Request

import ohmyadmin.components.table
from examples import icons
from examples.models import Address, Comment, Customer, Order, OrderItem
from ohmyadmin import components, filters, formatters
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
                        components.ModelField("Name", self.model.name),
                        components.ModelField(
                            "Email",
                            self.model.email,
                            formatter=formatters.Link(self.model.email, protocol="mailto"),
                        ),
                        components.ModelField(
                            "Phone",
                            self.model.phone,
                            formatter=formatters.Link(self.model.phone, protocol="tel"),
                        ),
                        components.ModelField("Birthdate", self.model.birthday),
                        components.Group(
                            label="Addresses",
                            children=[
                                ohmyadmin.components.table.Table[Address](
                                    items=self.model.addresses,
                                    headers=["Country", "City", "ZIP", "Street"],
                                    row_builder=lambda row: [
                                        ohmyadmin.components.table.TableColumn(row.country),
                                        ohmyadmin.components.table.TableColumn(row.city),
                                        ohmyadmin.components.table.TableColumn(row.zip),
                                        ohmyadmin.components.table.TableColumn(row.street),
                                    ],
                                ),
                            ],
                        ),
                        components.Group(
                            label="Payments",
                            children=[
                                ohmyadmin.components.table.Table(
                                    items=self.model.payments,
                                    headers=["Reference", "Currency", "Provider", "Method", "Amount"],
                                    row_builder=lambda row: [
                                        ohmyadmin.components.table.TableColumn(row.reference),
                                        ohmyadmin.components.table.TableColumn(row.currency_code),
                                        ohmyadmin.components.table.TableColumn(row.provider),
                                        ohmyadmin.components.table.TableColumn(row.method),
                                        ohmyadmin.components.table.TableColumn(
                                            row.amount,
                                            align="right",
                                            formatter=formatters.Number(prefix="$"),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        components.Group(
                            label="Orders",
                            children=[
                                ohmyadmin.components.table.Table(
                                    items=self.model.orders,
                                    headers=["Number", "Status", "Items", "Total price"],
                                    row_builder=lambda row: [
                                        ohmyadmin.components.table.TableColumn(row.number),
                                        ohmyadmin.components.table.TableColumn(row.status),
                                        ohmyadmin.components.table.TableColumn(
                                            ", ".join([str(item.product) for item in row.items])
                                        ),
                                        ohmyadmin.components.table.TableColumn(row.total_price),
                                    ],
                                ),
                            ],
                        ),
                        components.Group(
                            label="Comments",
                            children=[
                                ohmyadmin.components.table.Table(
                                    items=self.model.comments,
                                    headers=["Title", "Content", "Product", "Public", "Created at"],
                                    row_builder=lambda row: [
                                        ohmyadmin.components.table.TableColumn(row.title),
                                        ohmyadmin.components.table.TableColumn(row.content),
                                        ohmyadmin.components.table.TableColumn(row.product),
                                        ohmyadmin.components.table.TableColumn(
                                            row.public,
                                            value_builder=lambda value: components.BoolValue(value),
                                        ),
                                        ohmyadmin.components.table.TableColumn(row.created_at),
                                    ],
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
                    components.TableHeadCell("phone"),
                ]
            ),
            row_builder=lambda row: components.TableRow(
                children=[
                    components.TableColumn(
                        value_builder=lambda: components.Link(
                            text=row.name,
                            url=CustomerResource.get_edit_page_route(row.id),
                        )
                    ),
                    components.TableColumn(row.email, formatter=formatters.Link(protocol="mailto")),
                    components.TableColumn(row.phone, formatter=formatters.Link(protocol="tel")),
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
