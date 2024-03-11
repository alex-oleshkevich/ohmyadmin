import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from examples import icons
from examples.models import Address, Comment, Customer, Order, OrderItem
from ohmyadmin import components, filters, formatters
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.views.table import TableView


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
                                components.Table[Address](
                                    items=self.model.addresses,
                                    headers=["Country", "City", "ZIP", "Street"],
                                    row_builder=lambda row: [
                                        components.TableCell(row.country),
                                        components.TableCell(row.city),
                                        components.TableCell(row.zip),
                                        components.TableCell(row.street),
                                    ],
                                ),
                            ],
                        ),
                        components.Group(
                            label="Payments",
                            children=[
                                components.Table(
                                    items=self.model.payments,
                                    headers=["Reference", "Currency", "Provider", "Method", "Amount"],
                                    row_builder=lambda row: [
                                        components.TableCell(row.reference),
                                        components.TableCell(row.currency_code),
                                        components.TableCell(row.provider),
                                        components.TableCell(row.method),
                                        components.TableCell(
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
                                components.Table(
                                    items=self.model.orders,
                                    headers=["Number", "Status", "Items", "Total price"],
                                    row_builder=lambda row: [
                                        components.TableCell(row.number),
                                        components.TableCell(row.status),
                                        components.TableCell(", ".join([str(item.product) for item in row.items])),
                                        components.TableCell(row.total_price),
                                    ],
                                ),
                            ],
                        ),
                        components.Group(
                            label="Comments",
                            children=[
                                components.Table(
                                    items=self.model.comments,
                                    headers=["Title", "Content", "Product", "Public", "Created at"],
                                    row_builder=lambda row: [
                                        components.TableCell(row.title),
                                        components.TableCell(row.content),
                                        components.TableCell(row.product),
                                        components.TableCell(
                                            row.public,
                                            value_builder=lambda value: components.BoolValue(value),
                                        ),
                                        components.TableCell(row.created_at),
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
    form_view_class = CustomerFormView
    detail_view_class = CustomerDetailView
