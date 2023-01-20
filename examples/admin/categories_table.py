from examples.models import Category
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.pages.table import TablePage


class Categories(TablePage):
    icon = 'category'
    label = 'Categories (table)'
    datasource = SQLADataSource(Category)
