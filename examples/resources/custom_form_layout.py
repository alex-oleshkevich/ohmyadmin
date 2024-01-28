import anyio
import sqlalchemy as sa
import wtforms
from starlette.requests import Request
from starlette.responses import Response

from examples.models import Brand, Country
from ohmyadmin import htmx, components
from ohmyadmin.actions import actions
from ohmyadmin.datasources.sqlalchemy import load_choices
from ohmyadmin.components import BaseFormLayoutBuilder, Component
from ohmyadmin.screens.form import FormScreen


class AttributeForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    value = wtforms.IntegerField(validators=[wtforms.validators.data_required()])


class ManufacturerForm(wtforms.Form):
    name = wtforms.StringField()
    country = wtforms.SelectField(validators=[wtforms.validators.data_required()])


class ProductForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])
    brand_id = wtforms.SelectField()
    description = wtforms.TextAreaField()
    price = wtforms.DecimalField(validators=[wtforms.validators.data_required()])
    compare_at_price = wtforms.DecimalField(validators=[wtforms.validators.data_required()])
    cost_per_item = wtforms.DecimalField(
        description="Customers won't see this price.", validators=[wtforms.validators.data_required()]
    )
    images = wtforms.FieldList(wtforms.FileField(), min_entries=1)
    quantity = wtforms.IntegerField(default=0)
    sku = wtforms.IntegerField(default=0)
    security_stock = wtforms.IntegerField(
        default=0,
        description=(
            "The safety stock is the limit stock for your products which alerts you "
            "if the product stock will soon be out of stock."
        ),
    )
    barcode = wtforms.StringField(label="Barcode (ISBN, UPC, GTIN, etc.)")
    can_be_returned = wtforms.BooleanField(label="This product can be returned")
    can_be_shipped = wtforms.BooleanField(label="This product can be shipped")
    visible = wtforms.BooleanField(label="This product will be hidden from all sales channels.")
    availability = wtforms.BooleanField()
    manufacturer = wtforms.FormField(ManufacturerForm)
    attributes = wtforms.FieldList(wtforms.FormField(AttributeForm), min_entries=2)


class FormLayout(BaseFormLayoutBuilder):
    def build(self, form: ProductForm) -> Component:
        return components.Grid(
            children=[
                components.Column(
                    colspan=8,
                    children=[
                        components.Group(
                            label="Product info",
                            children=[
                                components.Grid(
                                    columns=2,
                                    children=[
                                        components.FormInput(form.name),
                                        components.FormInput(form.slug),
                                        components.FormInput(form.description, colspan=2),
                                    ],
                                ),
                            ],
                        ),
                        components.Group(
                            label="Image",
                            children=[
                                components.RepeatedFormInput(
                                    field=form.images,
                                    builder=lambda field: components.FormInput(field),
                                ),
                            ],
                        ),
                        components.Group(
                            label="Pricing",
                            description="Decide which communications you'd like to receive and how.",
                            children=[
                                components.Grid(
                                    columns=3,
                                    children=[
                                        components.FormInput(form.price),
                                        components.FormInput(form.compare_at_price),
                                        components.FormInput(form.cost_per_item),
                                    ],
                                ),
                            ],
                        ),
                        components.Group(
                            label="Inventory",
                            description="Decide which communications you'd like to receive and how.",
                            children=[
                                components.Grid(
                                    columns=3,
                                    children=[
                                        components.FormInput(form.sku),
                                        components.FormInput(form.barcode),
                                        components.FormInput(form.quantity),
                                        components.FormInput(form.security_stock, colspan=3),
                                    ],
                                )
                            ],
                        ),
                        components.Group(
                            label="Attributes",
                            children=[
                                components.RepeatedFormInput(
                                    form.attributes,
                                    builder=lambda field: components.Grid(
                                        columns=2,
                                        children=[
                                            components.FormInput(field.form.name),
                                            components.FormInput(field.form.value),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
                components.Column(
                    colspan=4,
                    children=[
                        components.Group(label="Brand", children=[components.FormInput(form.brand_id)]),
                        components.SeparatorComponent(),
                        components.Group(
                            label="",
                            children=[
                                components.FormInput(form.can_be_shipped),
                                components.FormInput(form.can_be_returned),
                            ],
                        ),
                        components.SeparatorComponent(),
                        components.Group(
                            label="Manufacturer",
                            children=[
                                components.NestedFormComponent(
                                    field=form.manufacturer,
                                    builder=lambda field: components.Column(
                                        children=[
                                            components.FormInput(field.form.name),
                                            components.FormInput(field.form.country),
                                        ]
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        )


class CustomProductFormView(FormScreen):
    label = "Custom form layout"
    group = "Views"
    description = "Demo of form view."
    form_class = ProductForm
    layout_class = FormLayout
    form_actions = [
        actions.SubmitAction(label="Submit", variant="accent", name="_save"),
        actions.SubmitAction(label="Submit and continue", name="_save_edit"),
        actions.LinkAction(url="/admin/", label="Cancel"),
    ]

    async def init_form(self, request: Request, form: ProductForm) -> None:
        async with anyio.create_task_group() as tg:
            tg.start_soon(load_choices, request.state.dbsession, form.brand_id, sa.select(Brand))
            tg.start_soon(load_choices, request.state.dbsession, form.manufacturer.country, sa.select(Country), "code")

    async def handle(self, request: Request, form: wtforms.Form) -> Response:
        print(form.data)
        return htmx.response().toast("Submitted!")
