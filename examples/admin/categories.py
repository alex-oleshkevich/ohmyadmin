import sqlalchemy as sa
import wtforms

from examples.models import Category
from ohmyadmin import formatters
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.contrib.sqlalchemy.utils import choices_from
from ohmyadmin.forms import AsyncSelectField
from ohmyadmin.resources import Resource
from ohmyadmin.views.table import TableColumn


class CategoryForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])
    parent_id = AsyncSelectField(choices=choices_from(Category), coerce=int)
    visible_to_customers = wtforms.BooleanField()
    description = wtforms.TextAreaField()


class Categories(Resource):
    icon = 'category'
    label_plural = 'Categories'
    datasource = SQLADataSource(Category, query=sa.select(Category).order_by(Category.name))
    form_class = CategoryForm
    columns = [
        TableColumn(name='name', searchable=True, sortable=True, link=True),
        TableColumn(name='visible_to_customers', formatter=formatters.BoolFormatter()),
        TableColumn(name='updated_at', formatter=formatters.DateTimeFormatter()),
    ]
