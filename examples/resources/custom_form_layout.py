import anyio
import sqlalchemy as sa
import wtforms
from starlette.requests import Request
from starlette.responses import Response

from examples.models import Brand, Country
from ohmyadmin import htmx, layouts
from ohmyadmin.datasources.sqlalchemy import load_choices
from ohmyadmin.layouts import BaseFormLayoutBuilder, Layout
from ohmyadmin.views.form import FormView


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
    def build(self, form: ProductForm) -> Layout:
        return layouts.GridLayout(
            children=[
                layouts.ColumnLayout(
                    colspan=8,
                    children=[
                        layouts.GroupLayout(
                            label="Product info",
                            children=[
                                layouts.GridLayout(
                                    columns=2,
                                    children=[
                                        layouts.FormInput(form.name),
                                        layouts.FormInput(form.slug),
                                        layouts.FormInput(form.description, colspan=2),
                                    ],
                                ),
                            ],
                        ),
                        layouts.GroupLayout(
                            label="Image",
                            children=[
                                layouts.RepeatedFormInput(
                                    field=form.images,
                                    builder=lambda field: layouts.FormInput(field),
                                ),
                            ],
                        ),
                        layouts.GroupLayout(
                            label="Pricing",
                            description="Decide which communications you'd like to receive and how.",
                            children=[
                                layouts.GridLayout(
                                    columns=3,
                                    children=[
                                        layouts.FormInput(form.price),
                                        layouts.FormInput(form.compare_at_price),
                                        layouts.FormInput(form.cost_per_item),
                                    ],
                                ),
                            ],
                        ),
                        layouts.GroupLayout(
                            label="Inventory",
                            description="Decide which communications you'd like to receive and how.",
                            children=[
                                layouts.GridLayout(
                                    columns=3,
                                    children=[
                                        layouts.FormInput(form.sku),
                                        layouts.FormInput(form.barcode),
                                        layouts.FormInput(form.quantity),
                                        layouts.FormInput(form.security_stock, colspan=3),
                                    ],
                                )
                            ],
                        ),
                        layouts.GroupLayout(
                            label="Attributes",
                            children=[
                                layouts.RepeatedFormInput(
                                    form.attributes,
                                    builder=lambda field: layouts.GridLayout(
                                        columns=2,
                                        children=[
                                            layouts.FormInput(field.form.name),
                                            layouts.FormInput(field.form.value),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
                layouts.ColumnLayout(
                    colspan=4,
                    children=[
                        layouts.GroupLayout(label="Brand", children=[layouts.FormInput(form.brand_id)]),
                        layouts.SeparatorLayout(),
                        layouts.GroupLayout(
                            label="",
                            children=[
                                layouts.FormInput(form.can_be_shipped),
                                layouts.FormInput(form.can_be_returned),
                            ],
                        ),
                        layouts.SeparatorLayout(),
                        layouts.GroupLayout(
                            label="Manufacturer",
                            children=[
                                layouts.NestedFormLayout(
                                    field=form.manufacturer,
                                    builder=lambda field: layouts.ColumnLayout(
                                        children=[
                                            layouts.FormInput(field.form.name),
                                            layouts.FormInput(field.form.country),
                                        ]
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        )


class CustomProductFormView(FormView):
    label = "Custom form layout"
    group = "Views"
    description = "Demo of form view."
    form_class = ProductForm
    layout_class = FormLayout
    form_actions = [
        # actions.SubmitAction(label="Submit", variant="accent", name="_save"),
        # actions.SubmitAction(label="Submit and continue", name="_save_edit"),
        # actions.LinkAction(url="/admin/", label="Cancel"),
    ]

    async def init_form(self, request: Request, form: ProductForm) -> None:
        async with anyio.create_task_group() as tg:
            tg.start_soon(load_choices, request.state.dbsession, form.brand_id, sa.select(Brand))
            tg.start_soon(load_choices, request.state.dbsession, form.manufacturer.country, sa.select(Country), "code")

    async def handle(self, request: Request, form: wtforms.Form) -> Response:
        print(form.data)
        return htmx.response().toast("Submitted!")
