import sqlalchemy as sa
import typing
import wtforms
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.admin.brands import BrandResource
from examples.models import Brand, Image, Product
from ohmyadmin import display
from ohmyadmin.display import DisplayField
from ohmyadmin.ext.sqla import (
    ChoiceFilter,
    DecimalFilter,
    FloatFilter,
    IntegerFilter,
    MultiChoiceFilter,
    SQLAlchemyResource,
    StringFilter,
    choices_from,
)
from ohmyadmin.filters import BaseFilter
from ohmyadmin.forms import AsyncFileField, AsyncForm, AsyncSelectField, FieldList, Uploader
from ohmyadmin.layout import Card, FormElement, Grid, Group, LayoutComponent
from ohmyadmin.metrics import Metric, ValueMetric


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


class ImageUploader(Uploader):
    def parse_entity_value(self, value: Image) -> typing.Any:
        if value:
            return value.image_path

    def set_file(self, entity: typing.Any, attr: str, filename: str) -> None:
        setattr(entity, attr, Image(image_path=filename))

    async def delete_file(self, entity: typing.Any, attr: str, filename: Image) -> None:
        if filename.image_path:
            await self.storage.delete(filename.image_path)


class ProductResource(SQLAlchemyResource):
    icon = 'assembly'
    entity_class = Product
    queryset = (
        sa.select(entity_class)
        .join(Brand)
        .options(
            joinedload(entity_class.brand),
            selectinload(entity_class.images),
            selectinload(entity_class.categories),
        )
    )

    def get_filters(self, request: Request) -> typing.Iterable[BaseFilter]:
        yield StringFilter(Product.name)
        yield ChoiceFilter(Product.brand_id, choices=choices_from(Brand), label='Brand', coerce=int)
        yield IntegerFilter(Product.sku)
        yield FloatFilter(Product.price)
        yield DecimalFilter(Product.cost_per_item)
        yield MultiChoiceFilter(
            Product.barcode, choices=[('5255323299388', '5255323299388'), ('5851908203322', '5851908203322')]
        )

    def get_metrics(self, request: Request) -> typing.Iterable[Metric]:
        yield TotalProducts()
        yield ProductInventory()
        yield AveragePrice()

    def _get_first_image(self, obj: Product) -> str | None:
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
        yield wtforms.StringField(name='name', validators=[wtforms.validators.data_required()])
        yield wtforms.StringField(name='slug', validators=[wtforms.validators.data_required()])
        yield wtforms.TextAreaField(name='description')
        yield wtforms.DecimalField(name='price', validators=[wtforms.validators.data_required()])
        yield wtforms.DecimalField(name='compare_at_price', validators=[wtforms.validators.data_required()])
        yield wtforms.DecimalField(
            name='cost_per_item',
            description="Customers won't see this price.",
            validators=[wtforms.validators.data_required()],
        )
        yield FieldList(
            name='images',
            unbound_field=AsyncFileField(
                uploader=ImageUploader(
                    storage=request.state.admin.file_storage,
                    upload_to='products/{prefix}_{file_name}',
                )
            ),
        )
        yield wtforms.IntegerField(name='sku', validators=[wtforms.validators.data_required()])
        yield wtforms.IntegerField(name='quantity', validators=[wtforms.validators.data_required()])
        yield wtforms.IntegerField(
            name='security_stock',
            validators=[wtforms.validators.data_required()],
            description=(
                'The safety stock is the limit stock for your products which alerts you '
                'if the product stock will soon be out of stock.'
            ),
        )
        yield wtforms.StringField(
            name='barcode', label='Barcode (ISBN, UPC, GTIN, etc.)', validators=[wtforms.validators.data_required()]
        )
        yield wtforms.BooleanField(name='can_be_returned', label='This product can be returned')
        yield wtforms.BooleanField(name='can_be_shipped', label='This product can be shipped')
        yield wtforms.BooleanField(name='visible', description='This product will be hidden from all sales channels.')
        yield wtforms.DateField(name='availability', validators=[wtforms.validators.data_required()])
        yield AsyncSelectField(name='brand_id', coerce=int, choices=choices_from(Brand))
        # categories = SelectMultipleField(required=True)

    def get_form_layout(self, request: Request, form: AsyncForm, instance: typing.Any) -> LayoutComponent:
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
                            label='Images',
                            children=[
                                FormElement(form.images),
                            ],
                        ),
                        Card(
                            label='Pricing',
                            columns=2,
                            children=[
                                FormElement(form.price),
                                FormElement(form.compare_at_price),
                                FormElement(form.cost_per_item),
                            ],
                        ),
                        Card(
                            label='Inventory',
                            columns=2,
                            children=[
                                FormElement(form.sku),
                                FormElement(form.barcode),
                                FormElement(form.quantity),
                                FormElement(form.security_stock),
                            ],
                        ),
                        Card(
                            label='Shipping',
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
                            label='Status',
                            children=[
                                FormElement(form.visible),
                                FormElement(form.availability),
                            ],
                        ),
                        Card(
                            label='Associations',
                            children=[
                                FormElement(form.brand_id),
                                # FormField(form.categories),
                            ],
                        ),
                    ],
                ),
            ],
        )
