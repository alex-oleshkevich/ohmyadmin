import typing

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.models import Product
from examples.resources.users_table import create_user_callback, CreateUserForm, PLUS_ICON, show_toast_callback
from ohmyadmin import formatters, components
from ohmyadmin.actions import actions
from ohmyadmin.views.display import BaseDisplayLayoutBuilder, DisplayView


class ProductLayout(BaseDisplayLayoutBuilder):
    def build(self, instance: Product) -> components.Component:
        return components.GridComponent(
            children=[
                components.GridComponent(
                    columns=12,
                    children=[
                        components.ColumnComponent(
                            colspan=6,
                            children=[
                                components.DisplayValueComponent(label="Name", value=instance.name),
                                components.DisplayValueComponent(
                                    label="Brand",
                                    value=instance.brand.name,
                                    formatter=formatters.LinkFormatter(
                                        url="/admin",
                                    ),
                                ),
                                components.DisplayValueComponent(
                                    label="Categories", value=", ".join([c.name for c in instance.categories]) or "-"
                                ),
                                components.GroupComponent(
                                    label="Pricing",
                                    children=[
                                        components.ColumnComponent(
                                            children=[
                                                components.DisplayValueComponent(
                                                    "Price",
                                                    instance.price,
                                                    formatter=formatters.NumberFormatter(prefix="$"),
                                                ),
                                                components.DisplayValueComponent(
                                                    "Compare at price",
                                                    instance.compare_at_price,
                                                    formatter=formatters.NumberFormatter(prefix="$"),
                                                ),
                                                components.DisplayValueComponent(
                                                    "Cost per item",
                                                    instance.cost_per_item,
                                                    formatter=formatters.NumberFormatter(prefix="$"),
                                                ),
                                            ]
                                        )
                                    ],
                                ),
                                components.GroupComponent(
                                    label="Inventory",
                                    children=[
                                        components.ColumnComponent(
                                            children=[
                                                components.DisplayValueComponent("SKU", instance.sku),
                                                components.DisplayValueComponent("Quantity", instance.quantity),
                                                components.DisplayValueComponent(
                                                    "Security stock", instance.security_stock
                                                ),
                                                components.DisplayValueComponent("Barcode", instance.barcode),
                                            ]
                                        ),
                                    ],
                                ),
                                components.DisplayValueComponent(label="Description", value=instance.description),
                            ],
                        ),
                        components.ColumnComponent(
                            colspan=6,
                            children=[
                                components.DisplayValueComponent(
                                    label="Visible",
                                    value=instance.visible,
                                    formatter=formatters.BoolFormatter(align="left"),
                                ),
                                components.DisplayValueComponent(
                                    label="Can be shipped",
                                    value=instance.can_be_shipped,
                                    formatter=formatters.BoolFormatter(align="left"),
                                ),
                                components.DisplayValueComponent(
                                    label="Can be returned",
                                    value=instance.can_be_returned,
                                    formatter=formatters.BoolFormatter(align="left"),
                                ),
                                components.SeparatorComponent(),
                                components.DisplayValueComponent(
                                    label="Availability",
                                    value=instance.availability,
                                    formatter=formatters.DateFormatter(),
                                ),
                                components.DisplayValueComponent(
                                    label="Created at",
                                    value=instance.created_at,
                                    formatter=formatters.DateFormatter(),
                                ),
                                components.DisplayValueComponent(
                                    label="Updated at",
                                    value=instance.updated_at,
                                    formatter=formatters.DateFormatter(),
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        )


class ProductView(DisplayView):
    label = "Display view"
    group = "Views"
    description = "Demo of display view."
    layout_class = ProductLayout
    object_actions = [
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

    async def get_object(self, request: Request) -> typing.Any:
        stmt = sa.select(Product).limit(1).options(joinedload(Product.brand), selectinload(Product.categories))
        result = await request.state.dbsession.execute(stmt)
        return result.scalars().one()
