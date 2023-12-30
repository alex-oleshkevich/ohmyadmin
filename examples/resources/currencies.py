import wtforms
import sqlalchemy as sa

from examples import icons
from examples.models import Currency
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.views.table import TableView


class CurrencyForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    code = wtforms.StringField(validators=[wtforms.validators.data_required()])


class CurrencyResource(ResourceScreen):
    group = "Shop"
    icon = icons.ICON_CURRENCY
    datasource = SADataSource(Currency, query=sa.select(Currency).order_by(Currency.name))
    form_class = CurrencyForm
    searchable_fields = (
        "name",
        "code",
    )
    ordering_fields = (
        "name",
        "code",
    )
    display_fields = (
        DisplayField("name"),
        DisplayField("code"),
    )
    index_view = TableView(
        columns=[
            DisplayField(name="name", link=True),
            DisplayField(name="code"),
        ]
    )
