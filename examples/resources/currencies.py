import wtforms
import sqlalchemy as sa
from starlette.requests import Request

from examples import icons
from examples.models import Currency
from ohmyadmin import components
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.resources.resource import ResourceScreen


class CurrencyForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    code = wtforms.StringField(validators=[wtforms.validators.data_required()])


class CurrencyDetailView(components.DetailView[Currency]):
    def compose(self, request: Request) -> components.Component:
        return components.Column(
            [
                components.ModelField("Code", components.Text(self.model.code)),
                components.ModelField("Name", components.Text(self.model.name)),
            ]
        )


class CurrencyFormView(components.FormView[CurrencyForm, Currency]):
    def compose(self, request: Request) -> components.Component:
        return components.Grid(
            children=[
                components.Column(
                    colspan=3,
                    children=[
                        components.FormInput(self.form.code),
                        components.FormInput(self.form.name),
                    ],
                ),
            ]
        )


class CurrencyIndexView(components.IndexView[Currency]):
    def compose(self, request: Request) -> components.Component:
        return components.Table(
            items=self.models,
            header=components.TableRow(
                children=[
                    components.TableSortableHeadCell("Code", sort_field="code"),
                    components.TableSortableHeadCell("Name", sort_field="name"),
                ]
            ),
            row_builder=lambda row: components.TableRow(
                children=[
                    components.TableColumn(
                        child=components.Link(text=str(row), url=CurrencyResource.get_edit_page_route(row.code)),
                    ),
                    components.TableColumn(components.Text(row.name)),
                ]
            ),
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
    index_view_class = CurrencyIndexView
    form_view_class = CurrencyFormView
    detail_view_class = CurrencyDetailView
