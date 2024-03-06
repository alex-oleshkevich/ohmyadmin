import wtforms
import sqlalchemy as sa
from starlette.requests import Request

from examples import icons
from examples.models import Currency
from ohmyadmin import components
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.views.table import TableView


class CurrencyForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    code = wtforms.StringField(validators=[wtforms.validators.data_required()])


class CurrencyDetailView(components.DetailView[Currency]):
    def build(self, request: Request) -> components.Component:
        return components.Column(
            [
                components.ModelField("Code", self.model.code),
                components.ModelField("Name", self.model.name),
            ]
        )


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
    index_view = TableView(
        columns=[
            DisplayField(name="name", link=True),
            DisplayField(name="code"),
        ]
    )
    detail_view_class = CurrencyDetailView
