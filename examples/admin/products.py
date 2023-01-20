import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import joinedload, selectinload

from examples.admin.brands import Brands
from examples.models import Brand, Product
from ohmyadmin import filters, formatters
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.helpers import LazyObjectURL
from ohmyadmin.resources import Resource
from ohmyadmin.views.table import TableColumn


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
    images = wtforms.FieldList(wtforms.FileField())
    sku = wtforms.IntegerField(default=0)
    security_stock = wtforms.IntegerField(
        default=0,
        description=(
            'The safety stock is the limit stock for your products which alerts you '
            'if the product stock will soon be out of stock.'
        ),
    )
    barcode = wtforms.StringField(label='Barcode (ISBN, UPC, GTIN, etc.)')
    can_be_returned = wtforms.BooleanField(label='This product can be returned')
    can_be_shipped = wtforms.BooleanField(label='This product can be shipped')
    visible = wtforms.BooleanField(label='This product will be hidden from all sales channels.')
    availability = wtforms.BooleanField()


class Products(Resource):
    icon = 'assembly'
    form_class = ProductForm
    datasource = SQLADataSource(
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
    filters = [
        filters.StringFilter('name'),
        filters.ChoiceFilter('brand_id', label='Brand', coerce=int, choices=[]),
        filters.IntegerFilter('sku'),
        filters.DecimalFilter('price'),
        filters.DecimalFilter('cost_per_item'),
        filters.MultiChoiceFilter(
            'barcode',
            choices=[
                ('5255323299388', '5255323299388'),
                ('5851908203322', '5851908203322'),
            ],
        ),
    ]
    columns = [
        # TableColumn('images'),
        TableColumn('name', sortable=True, searchable=True, link=True),
        TableColumn(
            'brand',
            searchable=True,
            search_in='brand.name',
            sortable=True,
            sort_by='brand.name',
            link=LazyObjectURL(lambda r, o: Brands.page_url(r, 'edit', pk=o.brand_id)),
        ),
        TableColumn('price', sortable=True, formatter=formatters.NumberFormatter(suffix='USD')),
        TableColumn('sku', sortable=True, formatter=formatters.NumberFormatter()),
        TableColumn('quantity', label='Qty.', sortable=True, formatter=formatters.NumberFormatter()),
        TableColumn('visible', formatter=formatters.BoolFormatter()),
    ]
