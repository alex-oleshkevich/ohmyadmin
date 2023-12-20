import typing

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.models import Product
from examples.resources.users_table import create_user_callback, CreateUserForm, PLUS_ICON, show_toast_callback
from ohmyadmin import formatters, layouts
from ohmyadmin.actions import actions
from ohmyadmin.views.display import BaseDisplayLayoutBuilder, DisplayView


class ProductLayout(BaseDisplayLayoutBuilder):
    def build(self, instance: Product) -> layouts.Layout:
        return layouts.GridLayout(
            children=[
                layouts.ColumnLayout(
                    colspan=6,
                    children=[
                        layouts.DisplayValueLayout(label="Name", value=instance.name),
                        layouts.DisplayValueLayout(
                            label="Brand",
                            value=instance.brand.name,
                            formatter=formatters.LinkFormatter(
                                url="/admin",
                            ),
                        ),
                        layouts.DisplayValueLayout(
                            label="Categories", value=", ".join([c.name for c in instance.categories]) or "-"
                        ),
                        layouts.DisplayValueLayout(
                            label="Visible", value=instance.visible, formatter=formatters.BoolFormatter(align="left")
                        ),
                        layouts.DisplayValueLayout(
                            label="Can be shipped",
                            value=instance.can_be_shipped,
                            formatter=formatters.BoolFormatter(align="left"),
                        ),
                        layouts.DisplayValueLayout(
                            label="Can be returned",
                            value=instance.can_be_returned,
                            formatter=formatters.BoolFormatter(align="left"),
                        ),
                        layouts.SeparatorLayout(),
                        layouts.DisplayValueLayout(
                            label="Availability",
                            value=instance.availability,
                            formatter=formatters.DateFormatter(),
                        ),
                        layouts.DisplayValueLayout(
                            label="Created at",
                            value=instance.created_at,
                            formatter=formatters.DateFormatter(),
                        ),
                        layouts.DisplayValueLayout(
                            label="Updated at",
                            value=instance.updated_at,
                            formatter=formatters.DateFormatter(),
                        ),
                        layouts.SeparatorLayout(),
                        layouts.GroupLayout(
                            label="Pricing",
                            children=[
                                layouts.ColumnLayout(
                                    children=[
                                        layouts.DisplayValueLayout(
                                            "Price", instance.price, formatter=formatters.NumberFormatter(prefix="$")
                                        ),
                                        layouts.DisplayValueLayout(
                                            "Compare at price",
                                            instance.compare_at_price,
                                            formatter=formatters.NumberFormatter(prefix="$"),
                                        ),
                                        layouts.DisplayValueLayout(
                                            "Cost per item",
                                            instance.cost_per_item,
                                            formatter=formatters.NumberFormatter(prefix="$"),
                                        ),
                                    ]
                                )
                            ],
                        ),
                        layouts.GroupLayout(
                            label="Inventory",
                            children=[
                                layouts.ColumnLayout(
                                    children=[
                                        layouts.DisplayValueLayout("SKU", instance.sku),
                                        layouts.DisplayValueLayout("Quantity", instance.quantity),
                                        layouts.DisplayValueLayout("Security stock", instance.security_stock),
                                        layouts.DisplayValueLayout("Barcode", instance.barcode),
                                    ]
                                ),
                            ],
                        ),
                        layouts.DisplayValueLayout(label="Description", value=instance.description),
                    ],
                )
            ]
        )


class ProductView(DisplayView):
    label = "Display view"
    group = "Views"
    description = "Demo of display view."
    layout_class = ProductLayout
    actions = [
        actions.LinkAction(url="/admin", label="To Main page"),
        actions.CallFunctionAction(function="alert", args=["kek"], label="Show alert"),
        actions.EventAction(event="refresh", variant="text", label="Refresh data"),
        actions.CallbackAction(show_toast_callback, label="Show toast", variant="danger"),
        actions.FormAction(
            icon=PLUS_ICON,
            label="New User",
            variant="accent",
            modal_title="Create user",
            form_class=CreateUserForm,
            callback=create_user_callback,
            modal_description="Create a new user right now!",
        ),
        # object_actions.LinkAction(url=lambda r, o: f"/admin?id={o.id}", label="Generated URL"),
        # object_actions.CallbackAction(label="Show toast", callback=object_toast_callback),
        # object_actions.CallbackAction(
        #     dangerous=True,
        #     label="Show toast with confirmation",
        #     callback=object_toast_callback,
        #     confirmation="Call this dangerous action?",
        # ),
        # object_actions.FormAction(
        #     label="Form action",
        #     callback=object_form_callback,
        #     form_class=RowObjectForm,
        #     icon=PLUS_ICON,
        # ),
        # object_actions.FormAction(
        #     label="Dangerous form action",
        #     dangerous=True,
        #     callback=object_form_callback,
        #     form_class=RowObjectForm,
        #     icon=PLUS_ICON,
        # ),
    ]

    async def get_object(self, request: Request) -> typing.Any:
        stmt = sa.select(Product).limit(1).options(joinedload(Product.brand), selectinload(Product.categories))
        result = await request.state.dbsession.execute(stmt)
        return result.scalars().one()