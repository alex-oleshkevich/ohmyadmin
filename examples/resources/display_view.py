import typing

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.models import Product
from examples.resources.users_table import create_user_callback, CreateUserForm, PLUS_ICON, show_toast_callback
from ohmyadmin import components, formatters
from ohmyadmin.actions import actions
from ohmyadmin.screens.display import DisplayScreen
from ohmyadmin.components import BaseDisplayLayoutBuilder
from ohmyadmin.views.display import BuilderDisplayView


class ProductLayout(BaseDisplayLayoutBuilder):
    def build(self, request: Request, model: Product) -> components.Component:
        return components.Grid(
            children=[
                components.Grid(
                    columns=12,
                    children=[
                        components.Column(
                            colspan=6,
                            children=[
                                components.DisplayValue(label="Name", value=model.name),
                                components.DisplayValue(
                                    label="Brand",
                                    value=model.brand.name,
                                    formatter=formatters.LinkFormatter(
                                        url="/admin",
                                    ),
                                ),
                                components.DisplayValue(
                                    label="Categories", value=", ".join([c.name for c in model.categories]) or "-"
                                ),
                                components.Group(
                                    label="Pricing",
                                    children=[
                                        components.Column(
                                            children=[
                                                components.DisplayValue(
                                                    "Price",
                                                    model.price,
                                                    formatter=formatters.NumberFormatter(prefix="$"),
                                                ),
                                                components.DisplayValue(
                                                    "Compare at price",
                                                    model.compare_at_price,
                                                    formatter=formatters.NumberFormatter(prefix="$"),
                                                ),
                                                components.DisplayValue(
                                                    "Cost per item",
                                                    model.cost_per_item,
                                                    formatter=formatters.NumberFormatter(prefix="$"),
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
                                                components.DisplayValue("SKU", model.sku),
                                                components.DisplayValue("Quantity", model.quantity),
                                                components.DisplayValue("Security stock", model.security_stock),
                                                components.DisplayValue("Barcode", model.barcode),
                                            ]
                                        ),
                                    ],
                                ),
                                components.DisplayValue(label="Description", value=model.description),
                            ],
                        ),
                        components.Column(
                            colspan=6,
                            children=[
                                components.DisplayValue(
                                    label="Visible",
                                    value=model.visible,
                                    formatter=formatters.BoolFormatter(align="left"),
                                ),
                                components.DisplayValue(
                                    label="Can be shipped",
                                    value=model.can_be_shipped,
                                    formatter=formatters.BoolFormatter(align="left"),
                                ),
                                components.DisplayValue(
                                    label="Can be returned",
                                    value=model.can_be_returned,
                                    formatter=formatters.BoolFormatter(align="left"),
                                ),
                                components.SeparatorComponent(),
                                components.DisplayValue(
                                    label="Availability",
                                    value=model.availability,
                                    formatter=formatters.DateFormatter(),
                                ),
                                components.DisplayValue(
                                    label="Created at",
                                    value=model.created_at,
                                    formatter=formatters.DateFormatter(),
                                ),
                                components.DisplayValue(
                                    label="Updated at",
                                    value=model.updated_at,
                                    formatter=formatters.DateFormatter(),
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
    view = BuilderDisplayView(ProductLayout())

    async def get_object(self, request: Request) -> typing.Any:
        stmt = sa.select(Product).limit(1).options(joinedload(Product.brand), selectinload(Product.categories))
        result = await request.state.dbsession.execute(stmt)
        return result.scalars().one()
