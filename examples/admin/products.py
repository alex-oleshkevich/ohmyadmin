import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.admin.brands import Brands
from examples.models import Brand, Product
from ohmyadmin import filters, formatters
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.helpers import LazyObjectURL
from ohmyadmin.metrics import ProgressMetric, TrendMetric, TrendResult, ValueMetric
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


class TotalProducts(ValueMetric):
    suffix = 'products'

    async def calculate(self, request: Request) -> str:
        stmt = sa.select(sa.func.count()).select_from(sa.select(Product).subquery())
        return await request.state.dbsession.scalar(stmt)


class AveragePrice(ValueMetric):
    async def calculate(self, request: Request) -> str:
        stmt = sa.select(sa.func.avg(Product.price)).select_from(Product)
        value = await request.state.dbsession.scalar(stmt)
        return f'${value:.2f} per item'


class Invisible(ProgressMetric):
    target = 100

    async def get_target(self, request: Request) -> int:
        stmt = sa.select(sa.func.count()).select_from(sa.select(Product).subquery())
        return await request.state.dbsession.scalar(stmt)

    async def current_value(self, request: Request) -> int | float:
        stmt = sa.select(sa.func.count()).select_from(sa.select(Product).where(Product.visible == False).subquery())
        return await request.state.dbsession.scalar(stmt)


class ProductsByYear(TrendMetric):
    label = 'Products by year'
    size = 6

    async def calculate(self, request: Request) -> TrendResult:
        stmt = (
            sa.select(
                sa.func.date_trunc('year', Product.created_at).label('year'),
                sa.func.count().label('total'),
            )
            .order_by(sa.text('1'))
            .group_by(sa.text('1'))
        )
        result = await request.state.dbsession.execute(stmt)
        return TrendResult(
            current_value=42,
            series=[(row.year.year, row.total) for row in result.all()],
        )


class Products(Resource):
    icon = 'assembly'
    form_class = ProductForm
    metrics = [TotalProducts, AveragePrice, Invisible, ProductsByYear, Invisible]
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
