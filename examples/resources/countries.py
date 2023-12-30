import wtforms

from examples.models import Country
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.display_fields import DisplayField
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
            DisplayField("code", link=True),
            DisplayField("name"),
        ]
    )
    display_fields = (
        DisplayField("code"),
        DisplayField("name"),
    )
