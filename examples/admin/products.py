import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload
from starlette.requests import Request

from examples.models import Product
from ohmyadmin.metrics import CountMetric
from ohmyadmin.resources import Resource
from ohmyadmin.tables import BoolColumn, Column, HasManyColumn, ImageColumn, NumberColumn


class TotalProducts(CountMetric):
    label = 'Total products'

    async def calc(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(sa.select(Product))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class ProductInventory(CountMetric):
    label = 'Product Inventory'

    async def calc(self, request: Request) -> int:
        stmt = sa.select(sa.func.sum(Product.quantity))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class AveragePrice(CountMetric):
    label = 'Average Price'
    value_prefix = 'USD'
    round = 2

    async def calc(self, request: Request) -> int:
        stmt = sa.select(sa.func.avg(Product.price))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class ProductResource(Resource):
    icon = 'assembly'
    entity_class = Product
    queryset = sa.select(entity_class).options(
        joinedload(entity_class.brand),
        selectinload(entity_class.images),
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
