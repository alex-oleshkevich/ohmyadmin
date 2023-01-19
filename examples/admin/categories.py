import sqlalchemy as sa
import wtforms

from examples.config import async_session
from examples.models import Category
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.resources import Resource
from ohmyadmin.views.table import TableColumn


class CategoryForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])


class CategoryResource(Resource):
    icon = 'category'
    label_plural = 'Categories'
    datasource = SQLADataSource(Category, async_session, query=sa.select(Category).order_by(Category.name))
    form_class = CategoryForm
    columns = [
        TableColumn(name='name', searchable=True, sortable=True),
    ]
