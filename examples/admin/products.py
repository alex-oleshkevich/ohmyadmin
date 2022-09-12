import pathlib
import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.models import Brand, Product
from ohmyadmin.forms import (
    Card,
    CheckboxField,
    DateField,
    DecimalField,
    Form,
    FormField,
    Grid,
    Group,
    IntegerField,
    Layout,
    MultipleFileField,
    SelectField,
    TextareaField,
    TextField,
    choices_from,
)
from ohmyadmin.metrics import CountMetric
from ohmyadmin.resources import Resource
from ohmyadmin.tables import BoolColumn, Column, HasManyColumn, ImageColumn, NumberColumn


class TotalProducts(CountMetric):
    label = 'Total products'

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(sa.select(Product))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class ProductInventory(CountMetric):
    label = 'Product Inventory'

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.sum(Product.quantity))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class AveragePrice(CountMetric):
    label = 'Average Price'
    value_prefix = 'USD'
    round = 2

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.avg(Product.price))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class ProductResource(Resource):
    icon = 'assembly'
    entity_class = Product
    queryset = sa.select(entity_class).options(
        joinedload(entity_class.brand),
        selectinload(entity_class.images),
        selectinload(entity_class.categories),
    )
    table_columns = [
        HasManyColumn('images', child=ImageColumn('image_path')),
        Column('name', sortable=True, searchable=True, link=True),
        Column(
            'brand', source='brand.name', searchable=True, search_in=['brand.name'], sortable=True, sort_by='brand.name'
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
    form_fields = [
        TextField('name', required=True),
        TextField('slug', required=True),
        TextareaField('description'),
        DecimalField('price', required=True),
        DecimalField('compare_at_price', required=True),
        DecimalField('cost_per_item', required=True, description="Customers won't see this price."),
        MultipleFileField(
            'images', upload_to=lambda file, entity: pathlib.Path('products') / str(entity.id) / file.filename
        ),
        IntegerField('sku', required=True),
        IntegerField('quantity', required=True),
        IntegerField(
            'security_stock',
            required=True,
            description=(
                'The safety stock is the limit stock for your products which alerts you '
                'if the product stock will soon be out of stock.'
            ),
        ),
        TextField('barcode', label='Barcode (ISBN, UPC, GTIN, etc.)', required=True),
        CheckboxField('can_be_returned', label='This product can be returned'),
        CheckboxField('can_be_shipped', label='This product can be shipped'),
        CheckboxField('visible', description='This product will be hidden from all sales channels.'),
        DateField('availability', required=True),
        SelectField('brand_id', coerce=int, choices=choices_from(Brand)),
        # SelectMultipleField('categories', required=True),
    ]

    def get_form_layout(self, request: Request, form: Form) -> Layout:
        return Grid(
            cols=3,
            children=[
                Group(
                    colspan=2,
                    children=[
                        Card(
                            columns=2,
                            children=[
                                FormField(form.name),
                                FormField(form.slug),
                                FormField(form.description, colspan='full'),
                            ],
                        ),
                        Card(
                            title='Images',
                            children=[
                                FormField(form.images),
                            ],
                        ),
                        Card(
                            title='Pricing',
                            columns=2,
                            children=[
                                FormField(form.price),
                                FormField(form.compare_at_price),
                                FormField(form.cost_per_item),
                            ],
                        ),
                        Card(
                            title='Inventory',
                            columns=2,
                            children=[
                                FormField(form.sku),
                                FormField(form.barcode),
                                FormField(form.quantity),
                                FormField(form.security_stock),
                            ],
                        ),
                        Card(
                            title='Shipping',
                            columns=2,
                            children=[
                                FormField(form.can_be_returned),
                                FormField(form.can_be_shipped),
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
                                FormField(form.visible),
                                FormField(form.availability),
                            ],
                        ),
                        Card(
                            title='Associations',
                            children=[
                                FormField(form.brand_id),
                                # FormField(form.categories),
                            ],
                        ),
                    ],
                ),
            ],
        )
