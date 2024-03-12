import contextlib

import slugify
import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request
from wtforms.fields.choices import SelectField

from examples import icons
from examples.models import Brand, Image, Product
from examples.resources.brands import BrandResource
from ohmyadmin import components, filters, formatters
from ohmyadmin.components import CellAlign
from ohmyadmin.datasources.sqlalchemy import form_choices_from, load_choices, SADataSource
from ohmyadmin.forms.utils import safe_int_coerce
from ohmyadmin.metrics import ProgressMetric, TrendMetric, TrendValue, ValueMetric, ValueValue
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.storages.uploaders import delete_file, upload_file


class ProductImageForm(wtforms.Form):
    image_path = wtforms.FileField(render_kw={"accept": "image/*"})
    delete = wtforms.BooleanField(render_kw={"style": "display: none"})


class ProductForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])
    brand_id = SelectField(validators=[wtforms.validators.data_required()], coerce=safe_int_coerce)
    description = wtforms.TextAreaField()
    price = wtforms.DecimalField(validators=[wtforms.validators.data_required()])
    compare_at_price = wtforms.DecimalField(validators=[wtforms.validators.data_required()])
    cost_per_item = wtforms.DecimalField(
        description="Customers won't see this price.", validators=[wtforms.validators.data_required()]
    )
    images = wtforms.FieldList(wtforms.FormField(form_class=ProductImageForm))

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
    availability = wtforms.DateField()


class TotalProducts(ValueMetric):
    formatter = formatters.String(suffix=" products")

    async def calculate(self, request: Request) -> ValueValue:
        stmt = sa.select(sa.func.count()).select_from(sa.select(Product).subquery())
        return await request.state.dbsession.scalar(stmt)


class AveragePrice(ValueMetric):
    formatter = formatters.Number(suffix=" per item", decimals=2, prefix="$")

    async def calculate(self, request: Request) -> ValueValue:
        stmt = sa.select(sa.func.avg(Product.price)).select_from(Product)
        return await request.state.dbsession.scalar(stmt)


class Invisible(ProgressMetric):
    target = 100

    async def get_target(self, request: Request) -> int:
        stmt = sa.select(sa.func.count()).select_from(sa.select(Product).subquery())
        return await request.state.dbsession.scalar(stmt)

    async def calculate(self, request: Request) -> int | float:
        stmt = sa.select(sa.func.count()).select_from(sa.select(Product).where(Product.visible == False).subquery())
        return await request.state.dbsession.scalar(stmt)


class ProductsByYear(TrendMetric):
    label = "Products by year"

    async def calculate(self, request: Request) -> list[TrendValue]:
        stmt = (
            sa.select(
                sa.func.date_trunc("year", Product.created_at).label("year"),
                sa.func.count().label("total"),
            )
            .order_by(sa.text("1"))
            .group_by(sa.text("1"))
        )
        result = await request.state.dbsession.execute(stmt)
        return [TrendValue(label=row.year.year, value=row.total) for row in result.all()]


class ProductDetailView(components.DetailView[Product]):
    def build(self, request: Request) -> components.Component:
        return components.Grid(
            columns=2,
            children=[
                components.Column(
                    colspan=1,
                    children=[
                        components.Group(
                            label="Product",
                            children=[
                                components.ModelField("Name", components.Text(self.model.name)),
                                components.ModelField("Slug", components.Text(self.model.slug)),
                                components.ModelField("Description", components.Text(self.model.description)),
                            ],
                        ),
                        components.Group(
                            label="Pricing",
                            description="This information will be displayed publicly so be careful what you share.",
                            children=[
                                components.ModelField(
                                    "Price",
                                    components.Text(
                                        self.model.price,
                                        formatter=formatters.Number(prefix="$"),
                                    ),
                                ),
                                components.ModelField(
                                    "Compare at price",
                                    components.Text(
                                        self.model.compare_at_price,
                                        formatter=formatters.Number(prefix="$"),
                                    ),
                                ),
                                components.ModelField(
                                    "Cost per item",
                                    components.Text(
                                        self.model.cost_per_item,
                                        formatter=formatters.Number(prefix="$"),
                                    ),
                                ),
                            ],
                        ),
                        components.Group(
                            label="Inventory",
                            description="Decide which communications you'd like to receive and how.",
                            children=[
                                components.ModelField(
                                    "SKU",
                                    components.Text(
                                        self.model.sku,
                                        formatter=formatters.Number(),
                                    ),
                                ),
                                components.ModelField("Barcode", components.Text(self.model.barcode)),
                                components.ModelField(
                                    "Quantity",
                                    components.Text(
                                        self.model.quantity,
                                        formatter=formatters.Number(),
                                    ),
                                ),
                                components.ModelField(
                                    "Security stock",
                                    components.Text(
                                        self.model.security_stock,
                                        formatter=formatters.Number(),
                                    ),
                                ),
                            ],
                        ),
                        components.Group(
                            label="Images",
                            children=[
                                components.Grid(
                                    columns=4,
                                    children=[components.Image(image.image_path) for image in self.model.images],
                                )
                            ],
                        ),
                    ],
                ),
                components.Column(
                    colspan=1,
                    children=[
                        components.Group(
                            label="Brand",
                            children=[
                                components.ModelField(
                                    "Brand",
                                    components.Link(
                                        text=self.model.brand.name,
                                        url=BrandResource.get_display_page_route(self.model.brand_id),
                                    ),
                                ),
                            ],
                        ),
                        components.Group(
                            label="Shipment",
                            children=[
                                components.ModelField(
                                    "Can be shipped",
                                    components.BoolValue(self.model.can_be_shipped),
                                ),
                                components.ModelField(
                                    "Can be returned",
                                    components.BoolValue(self.model.can_be_returned),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )


class ProductFormView(components.FormView[ProductForm, Product]):
    def build(self, request: Request) -> components.Component:
        return components.Grid(
            columns=12,
            children=[
                components.Column(
                    colspan=8,
                    children=[
                        components.Group(
                            label="Product",
                            children=[
                                components.FormInput(self.form.name),
                                components.FormInput(self.form.slug),
                                components.FormInput(self.form.description),
                            ],
                        ),
                        components.Group(
                            label="Images",
                            children=[
                                components.RepeatedFormInput(
                                    self.form.images,
                                    builder=lambda f: components.Column(
                                        children=[
                                            components.ImageFormInput(
                                                f,
                                                media_url=f.image_path.data if f.image_path.data else None,
                                            ),
                                        ]
                                    ),
                                )
                            ],
                        ),
                        components.Group(
                            label="Pricing",
                            children=[
                                components.Grid(
                                    children=[
                                        components.FormInput(self.form.price, colspan=3),
                                        components.FormInput(self.form.compare_at_price, colspan=3),
                                        components.FormInput(self.form.cost_per_item, colspan=6),
                                    ]
                                ),
                            ],
                            description="This information will be displayed publicly so be careful what you share.",
                        ),
                        components.Group(
                            label="Inventory",
                            children=[
                                components.Grid(
                                    columns=12,
                                    children=[
                                        components.FormInput(self.form.barcode, colspan=4),
                                        components.FormInput(self.form.quantity, colspan=4),
                                        components.FormInput(self.form.sku, colspan=4),
                                        components.FormInput(self.form.security_stock, colspan=12),
                                    ],
                                ),
                            ],
                            description="Decide which communications you'd like to receive and how.",
                        ),
                    ],
                ),
                components.Column(
                    colspan=4,
                    children=[
                        components.Group(
                            label="Brand",
                            children=[
                                components.FormInput(self.form.brand_id),
                            ],
                        ),
                        components.Group(
                            label="Shipment",
                            children=[
                                components.FormInput(self.form.availability),
                                components.FormInput(self.form.can_be_shipped),
                                components.FormInput(self.form.can_be_returned),
                            ],
                        ),
                    ],
                ),
            ],
        )


class ProductIndexView(components.IndexView[Product]):
    def build(self, request: Request) -> components.Component:
        return components.Table(
            items=self.models,
            header=components.TableRow(
                children=[
                    components.TableSortableHeadCell("Name", sort_field="name"),
                    components.TableSortableHeadCell("Brand", sort_field="brand__name"),
                    components.TableSortableHeadCell("SKU", sort_field="sku", align=CellAlign.RIGHT),
                    components.TableSortableHeadCell("Price", sort_field="price", align=CellAlign.RIGHT),
                    components.TableSortableHeadCell("Quantity", sort_field="quantity", align=CellAlign.RIGHT),
                    components.TableHeadCell("Visible", align=CellAlign.CENTER),
                ]
            ),
            row_builder=lambda row: components.TableRow(
                children=[
                    components.TableColumn(
                        child=components.Link(text=row.name, url=ProductResource.get_edit_page_route(row.id))
                    ),
                    components.TableColumn(
                        child=components.Link(
                            text=row.brand.name, url=BrandResource.get_display_page_route(row.brand_id)
                        )
                    ),
                    components.TableColumn(
                        components.Text(row.price, formatter=formatters.Number(prefix="$ ")), align=CellAlign.RIGHT
                    ),
                    components.TableColumn(
                        components.Text(row.sku, formatter=formatters.Number()), align=CellAlign.RIGHT
                    ),
                    components.TableColumn(
                        components.Text(row.quantity, formatter=formatters.Number()), align=CellAlign.RIGHT
                    ),
                    components.TableColumn(components.BoolValue(row.visible), align=CellAlign.CENTER),
                ]
            ),
        )


class ProductResource(ResourceScreen):
    icon = icons.ICON_PRODUCTS
    group = "Shop"
    form_class = ProductForm
    page_metrics = [ProductsByYear(), TotalProducts(), AveragePrice()]
    datasource = SADataSource(
        Product,
        query=(
            sa.select(Product)
            .join(Brand)
            .options(
                joinedload(Product.brand),
                selectinload(Product.images),
                selectinload(Product.categories),
            )
        ),
    )
    page_filters = [
        filters.StringFilter("name"),
        filters.ChoiceFilter("brand_id", label="Brand", coerce=safe_int_coerce, choices=form_choices_from(Brand)),
        filters.IntegerFilter("sku"),
        filters.DecimalFilter("price"),
        filters.DecimalFilter("cost_per_item"),
        filters.MultiChoiceFilter(
            "barcode",
            choices=[
                ("5255323299388", "5255323299388"),
                ("5851908203322", "5851908203322"),
            ],
        ),
    ]
    ordering_fields = "name", "brand", "price", "sku", "quantity"  # FIXME: nested ordering = brand.name
    searchable_fields = ("name", "brand")  # FIXME: nested search = brand.name
    index_view_class = ProductIndexView
    detail_view_class = ProductDetailView
    form_view_class = ProductFormView

    async def init_form(self, request: Request, form: ProductForm) -> None:
        await load_choices(request.state.dbsession, form.brand_id, sa.select(Brand))

    async def populate_object(self, request: Request, form: ProductForm, model: Product) -> None:
        images = model.images
        for image_form in form.images:
            if image_form.delete.data:
                images.remove(image_form.object_data)
                with contextlib.suppress(FileNotFoundError):
                    await delete_file(request, image_form.image_path.data)
                continue

            if image_form.image_path.data:
                path = await upload_file(
                    request,
                    image_form.image_path.data,
                    "products/{group_name}/{random}_{basename}",
                    tokens={"group_name": slugify.slugify(form.name.data)},
                )
                images.append(Image(image_path=path))
        del form.images

        await super().populate_object(request, form, model)
