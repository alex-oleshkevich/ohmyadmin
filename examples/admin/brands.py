import sqlalchemy as sa
import wtforms

from examples.models import Brand
from ohmyadmin import formatters
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.filters import ChoiceFilter
from ohmyadmin.resources import Resource
from ohmyadmin.views.table import TableColumn


class BrandForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])
    website = wtforms.URLField()
    visible_to_customers = wtforms.BooleanField()
    description = wtforms.TextAreaField()


class Brands(Resource):
    icon = 'basket'
    datasource = SQLADataSource(Brand, sa.select(Brand).order_by(Brand.name))
    form_class = BrandForm
    filters = [
        ChoiceFilter(
            'website',
            choices=[
                ('http://simpson.com/', 'Simpson'),
                ('http://ross.com/', 'Ross'),
            ],
        ),
    ]
    columns = [
        TableColumn('name', searchable=True, sortable=True, link=True),
        TableColumn('website'),
        TableColumn('visible_to_customers', label='Visibility', formatter=formatters.BoolFormatter(as_text=True)),
        TableColumn('updated_at', formatter=formatters.DateTimeFormatter()),
    ]
