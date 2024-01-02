import wtforms

from examples import icons
from examples.models import Country
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.views.display import AutoDisplayView
from ohmyadmin.views.table import TableView


class CountryForm(wtforms.Form):
    code = wtforms.StringField(validators=[wtforms.validators.data_required()])
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])


class CountryResource(ResourceScreen):
    group = "Shop"
    icon = icons.ICON_COUNTRIES
    datasource = SADataSource(Country)
    form_class = CountryForm
    index_view = TableView(
        columns=[
            DisplayField("code", link=True),
            DisplayField("name"),
        ]
    )
    display_view = AutoDisplayView(
        fields=[
            DisplayField("code"),
            DisplayField("name"),
        ]
    )
