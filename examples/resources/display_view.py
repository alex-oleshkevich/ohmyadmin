import typing

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.models import Product
from examples.resources.brands import BrandResource
from examples.resources.users_table import create_user_callback, CreateUserForm, PLUS_ICON, show_toast_callback
from ohmyadmin import components, formatters
from ohmyadmin.actions import actions
from ohmyadmin.screens.display import DisplayScreen


class ProductDetailView(components.DetailView[Product]):
    def build(self, request: Request) -> components.Component:
        return components.Grid(
            children=[
                components.Grid(
                    columns=12,
                    children=[
                        components.Column(
                            colspan=6,
                            children=[
                                components.ModelField(label="Name", value=self.model.name),
                                components.ModelField(
                                    label="Brand",
                                    value=self.model.brand.name,
                                    value_builder=lambda _: components.Link(
                                        url=BrandResource.get_display_page_route(self.model.brand_id),
                                        text=self.model.brand,
                                    ),
                                ),
                                components.ModelField(
                                    label="Categories", value=", ".join([c.name for c in self.model.categories]) or "-"
                                ),
                                components.Group(
                                    label="Pricing",
                                    children=[
                                        components.Column(
                                            children=[
                                                components.ModelField(
                                                    "Price",
                                                    self.model.price,
                                                    formatter=formatters.Number(prefix="$"),
                                                ),
                                                components.ModelField(
                                                    "Compare at price",
                                                    self.model.compare_at_price,
                                                    formatter=formatters.Number(prefix="$"),
                                                ),
                                                components.ModelField(
                                                    "Cost per item",
                                                    self.model.cost_per_item,
                                                    formatter=formatters.Number(prefix="$"),
                                                ),
                                            ]
                                        )
                                    ],
                                ),
                                components.Group(
                                    label="Inventory",
                                    children=[
                                        components.Column(
                                            children=[
                                                components.ModelField("SKU", self.model.sku),
                                                components.ModelField("Quantity", self.model.quantity),
                                                components.ModelField("Security stock", self.model.security_stock),
                                                components.ModelField("Barcode", self.model.barcode),
                                            ]
                                        ),
                                    ],
                                ),
                                components.ModelField(label="Description", value=self.model.description),
                            ],
                        ),
                        components.Column(
                            colspan=6,
                            children=[
                                components.Group(
                                    children=[
                                        components.ModelField(
                                            label="Visible",
                                            value=self.model.visible,
                                            value_builder=lambda value: components.BoolValue(value),
                                        ),
                                        components.ModelField(
                                            label="Can be shipped",
                                            value=self.model.can_be_shipped,
                                            value_builder=lambda value: components.BoolValue(value),
                                        ),
                                        components.ModelField(
                                            label="Can be returned",
                                            value=self.model.can_be_returned,
                                            value_builder=lambda value: components.BoolValue(value),
                                        ),
                                    ]
                                ),
                                components.Group(
                                    children=[
                                        components.ModelField(label="Availability", value=self.model.availability),
                                        components.ModelField(label="Created at", value=self.model.created_at),
                                        components.ModelField(label="Updated at", value=self.model.updated_at),
                                    ]
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        )


class ProductView(DisplayScreen):
    label = "Display view"
    group = "Views"
    description = "Demo of display view."
    page_actions = [
        actions.LinkAction(url="/admin", label="To Main page"),
        actions.CallbackAction(callback=show_toast_callback, label="Show toast", variant="danger"),
        actions.ModalAction(
            icon=PLUS_ICON,
            label="New User",
            variant="accent",
            modal_title="Create user",
            form_class=CreateUserForm,
            callback=create_user_callback,
            modal_description="Create a new user right now!",
        ),
    ]
    view_class = ProductDetailView

    async def get_object(self, request: Request) -> typing.Any:
        stmt = sa.select(Product).limit(1).options(joinedload(Product.brand), selectinload(Product.categories))
        result = await request.state.dbsession.execute(stmt)
        return result.scalars().one()
