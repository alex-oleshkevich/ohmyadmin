import sqlalchemy as sa
import wtforms

from examples.models import Currency
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.resources import Resource
from ohmyadmin.views.table import TableColumn


class CurrencyForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])


class Currencies(Resource):
    icon = 'currency'
    label_plural = 'Currencies'
    datasource = SQLADataSource(Currency, query=sa.select(Currency).order_by(Currency.name))
    form_class = CurrencyForm
    columns = [
        TableColumn(name='name', searchable=True, sortable=True, link=True),
        TableColumn(name='code', searchable=True),
    ]
