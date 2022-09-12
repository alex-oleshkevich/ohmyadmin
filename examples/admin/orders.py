import sqlalchemy as sa
from starlette.requests import Request

from examples.models import Order
from ohmyadmin.metrics import CountMetric
from ohmyadmin.resources import Resource
from ohmyadmin.tables import Column


class TotalOrders(CountMetric):
    label = 'Orders'

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(sa.select(Order))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class OpenOrders(CountMetric):
    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.count('*')).select_from(sa.select(Order).where(Order.status == 'New'))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class AveragePrice(CountMetric):
    value_prefix = 'USD'
    round = 2

    async def calculate(self, request: Request) -> int:
        stmt = sa.select(sa.func.avg(Order.price))
        result = await request.state.dbsession.scalars(stmt)
        return result.one()


class OrderResource(Resource):
    icon = 'shopping-cart'
    entity_class = Order
    metrics = [
        TotalOrders(),
        OpenOrders(),
        AveragePrice(),
    ]
    table_columns = [
        Column('number', searchable=True, link=True),
        # Column('customer'),
        Column('status', sortable=True),
        Column('currency'),
        Column('total_price'),
        Column('shipping_cost'),
        Column('created_at', label='Order date'),
    ]
