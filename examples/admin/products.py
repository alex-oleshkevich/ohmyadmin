import pathlib
import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.admin.brands import BrandResource
from examples.models import Brand, Product
from ohmyadmin.components import Card, Component, FormElement, Grid, Group
from ohmyadmin.metrics import ValueMetric
from ohmyadmin.old_forms import (
    CheckboxField,
    DateField,
    DecimalField,
    Form,
    IntegerField,
    MultipleFileField,
    SelectField,
    TextareaField,
    TextField,
    choices_from,
)
from ohmyadmin.resources import Resource
from ohmyadmin.tables import BoolColumn, Column, HasManyColumn, ImageColumn, NumberColumn


class TotalProducts(ValueMetric):
    label = 'Total products'

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(sa.select(Product))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class ProductInventory(ValueMetric):
    label = 'Product Inventory'

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.sum(Product.quantity))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class AveragePrice(ValueMetric):
    label = 'Average Price'
    value_prefix = 'USD'
    round = 2

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.avg(Product.price))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class EditForm(Form):
    name = TextField(required=True)
    slug = TextField(required=True)
    description = TextareaField()
    price = DecimalField(required=True)
    compare_at_price = DecimalField(required=True)
    cost_per_item = DecimalField(required=True, description="Customers won't see this price.")
    images = MultipleFileField(upload_to=lambda file, entity: pathlib.Path('products') / str(entity.id) / file.filename)
    sku = IntegerField(required=True)
    quantity = IntegerField(required=True)
    security_stock = IntegerField(
        required=True,
        description=(
            'The safety stock is the limit stock for your products which alerts you '
            'if the product stock will soon be out of stock.'
        ),
    )
    barcode = TextField(label='Barcode (ISBN, UPC, GTIN, etc.)', required=True)
    can_be_returned = CheckboxField(label='This product can be returned')
    can_be_shipped = CheckboxField(label='This product can be shipped')
    visible = CheckboxField(description='This product will be hidden from all sales channels.')
    availability = DateField(required=True)
    brand_id = SelectField(coerce=int, choices=choices_from(Brand))
    # categories = SelectMultipleField(required=True)


class ProductResource(Resource):
    icon = 'assembly'
    entity_class = Product
    form_class = EditForm
    queryset = (
        sa.select(entity_class)
        .join(Brand)
        .options(
            joinedload(entity_class.brand),
            selectinload(entity_class.images),
            selectinload(entity_class.categories),
        )
    )
    table_columns = [
        HasManyColumn('images', child=ImageColumn('image_path')),
        Column('name', sortable=True, searchable=True, link=True),
        Column(
            'brand',
            searchable=True,
            search_in='brand.name',
            sortable=True,
            sort_by=Brand.name,
            link_factory=lambda r, o: r.url_for(BrandResource.url_name('edit'), pk=o.brand.id),
        ),
        NumberColumn('price', sortable=True),
        NumberColumn('sku', sortable=True),
        NumberColumn('quantity', label='Qty', sortable=True),
        BoolColumn('visible', label='Visibility'),
    ]
    metrics = [
        TotalProducts(),
        ProductInventory(),
        AveragePrice(),
    ]

    def get_form_layout(self, request: Request, form: Form) -> Component:
        return Grid(
            columns=3,
            children=[
                Group(
                    colspan=2,
                    children=[
                        Card(
                            columns=2,
                            children=[
                                FormElement(form.name),
                                FormElement(form.slug),
                                FormElement(form.description, colspan='full'),
                            ],
                        ),
                        Card(
                            title='Images',
                            children=[
                                FormElement(form.images),
                            ],
                        ),
                        Card(
                            title='Pricing',
                            columns=2,
                            children=[
                                FormElement(form.price),
                                FormElement(form.compare_at_price),
                                FormElement(form.cost_per_item),
                            ],
                        ),
                        Card(
                            title='Inventory',
                            columns=2,
                            children=[
                                FormElement(form.sku),
                                FormElement(form.barcode),
                                FormElement(form.quantity),
                                FormElement(form.security_stock),
                            ],
                        ),
                        Card(
                            title='Shipping',
                            columns=2,
                            children=[
                                FormElement(form.can_be_returned),
                                FormElement(form.can_be_shipped),
                            ],
                        ),
                    ],
                ),
                Group(
                    colspan=1,
                    children=[
                        Card(
                            title='Status',
                            children=[
                                FormElement(form.visible),
                                FormElement(form.availability),
                            ],
                        ),
                        Card(
                            title='Associations',
                            children=[
                                FormElement(form.brand_id),
                                # FormField(form.categories),
                            ],
                        ),
                    ],
                ),
            ],
        )
