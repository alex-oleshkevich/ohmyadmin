import pathlib
import sqlalchemy as sa
import typing
import wtforms
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.admin.brands import BrandResource
from examples.models import Brand, Product
from ohmyadmin.components import Card, Component, FormElement, Grid, Group, display
from ohmyadmin.components.display import DisplayField
from ohmyadmin.ext.sqla import SQLAlchemyResource
from ohmyadmin.forms import (
    BooleanField,
    DateField,
    DecimalField,
    Form,
    IntegerField,
    MultipleFileField,
    SelectField,
    StringField,
    TextAreaField,
)
from ohmyadmin.metrics import ValueMetric
from ohmyadmin.old_forms import choices_from


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


class ProductResource(SQLAlchemyResource):
    icon = 'assembly'
    entity_class = Product
    label_plural = 'Produkty'
    queryset = (
        sa.select(entity_class)
        .join(Brand)
        .options(
            joinedload(entity_class.brand),
            selectinload(entity_class.images),
            selectinload(entity_class.categories),
        )
    )
    metrics = [
        TotalProducts(),
        ProductInventory(),
        AveragePrice(),
    ]

    def _get_first_image(self, obj):
        if obj.images:
            return obj.images[0].image_path
        return None

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        yield DisplayField('images', value_getter=self._get_first_image, component=display.Image())
        yield DisplayField('name', sortable=True, searchable=True, link=True)
        yield DisplayField(
            'brand',
            searchable=True,
            search_in='brand.name',
            sortable=True,
            sort_by='brand.name',
            link=lambda req, obj: req.url_for(BrandResource.url_name('edit'), pk=obj.brand.id),
        )
        yield DisplayField('price', sortable=True, component=display.Money(currency='USD'))
        yield DisplayField('sku', sortable=True, component=display.Number())
        yield DisplayField('quantity', label='Qty', sortable=True, component=display.Number())
        yield DisplayField('visible', label='Visibility', component=display.Boolean())

    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        yield StringField(name='name', required=True)
        yield StringField(name='slug', required=True)
        yield TextAreaField(name='description')
        yield DecimalField(name='price', required=True)
        yield DecimalField(name='compare_at_price', required=True)
        yield DecimalField(name='cost_per_item', required=True, description="Customers won't see this price.")
        yield MultipleFileField(
            name='images', upload_to=lambda file, entity: pathlib.Path('products') / str(entity.id) / file.filename
        )
        yield IntegerField(name='sku', required=True)
        yield IntegerField(name='quantity', required=True)
        yield IntegerField(
            name='security_stock',
            required=True,
            description=(
                'The safety stock is the limit stock for your products which alerts you '
                'if the product stock will soon be out of stock.'
            ),
        )
        yield StringField(name='barcode', label='Barcode (ISBN, UPC, GTIN, etc.)', required=True)
        yield BooleanField(name='can_be_returned', label='This product can be returned')
        yield BooleanField(name='can_be_shipped', label='This product can be shipped')
        yield BooleanField(name='visible', description='This product will be hidden from all sales channels.')
        yield DateField(name='availability', required=True)
        yield SelectField(name='brand_id', coerce=int, choices=choices_from(Brand))
        # categories = SelectMultipleField(required=True)

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
