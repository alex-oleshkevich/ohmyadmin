import wtforms

from examples.models import Country
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.screens.table import Column
from ohmyadmin.views.table import TableView


class CountryForm(wtforms.Form):
    code = wtforms.StringField(validators=[wtforms.validators.data_required()])
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])


class CountriesResource(ResourceScreen):
    label = "Country"
    group = "Shop"
    datasource = SADataSource(Country)
    form_class = CountryForm
    index_view = TableView(
        columns=[
            Column("code"),
            Column("name"),
        ]
    )
