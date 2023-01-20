import sqlalchemy as sa
from sqlalchemy.orm import joinedload, selectinload

from examples.admin.brands import Brands
from examples.models import Brand, Product
from ohmyadmin import formatters
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.helpers import LazyObjectURL
from ohmyadmin.pages.table import TablePage
from ohmyadmin.views.table import TableColumn


class ProductsPage(TablePage):
    icon = 'assembly'
    group = 'Pages'
    label_plural = 'Products'
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
