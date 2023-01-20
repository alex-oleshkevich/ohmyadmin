import sqlalchemy as sa
import wtforms

from examples.models import Customer
from ohmyadmin import filters
from ohmyadmin.contrib.sqlalchemy import SQLADataSource
from ohmyadmin.resources import Resource
from ohmyadmin.views.table import TableColumn


class CustomerForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    email = wtforms.EmailField(validators=[wtforms.validators.data_required()])
    phone = wtforms.TelField()
    birthday = wtforms.DateField()


class Customers(Resource):
    icon = 'friends'
    datasource = SQLADataSource(Customer, sa.select(Customer).order_by(Customer.name))
    form_class = CustomerForm
    filters = [
        filters.DateFilter('created_at'),
        filters.DateFilter('birthday'),
    ]
    columns = [
        TableColumn('name', sortable=True, searchable=True, link=True),
        TableColumn('email', sortable=True, searchable=True),
        TableColumn('phone', searchable=True),
    ]
