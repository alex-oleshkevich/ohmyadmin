import sqlalchemy as sa
import wtforms

from examples.models import Country
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.resources import Resource
from ohmyadmin.views.table import TableColumn


class CountryForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    code = wtforms.StringField(validators=[wtforms.validators.data_required()])


class Countries(Resource):
    icon = 'map'
    form_class = CountryForm
    datasource = SQLADataSource(Country, sa.select(Country).order_by(Country.name))
    columns = [
        TableColumn('name', searchable=True, sortable=True, link=True),
        TableColumn('code', searchable=True),
    ]
