import wtforms
from starlette.requests import Request

from examples import icons
from examples.models import Country
from ohmyadmin import components
from ohmyadmin.components import Component
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.resources.resource import ResourceScreen


class CountryForm(wtforms.Form):
    code = wtforms.StringField(validators=[wtforms.validators.data_required()])
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])


class CountryDetailView(components.DetailView[Country]):
    def build(self, request: Request) -> components.Component:
        return components.Column(
            [
                components.ModelField("Code", self.model.code),
                components.ModelField("Name", self.model.name),
            ]
        )


class FormView(components.FormView[CountryForm, Country]):
    def build(self, request: Request) -> Component:
        return components.Grid(
            children=[
                components.Column(
                    colspan=6,
                    children=[
                        components.FormInput(self.form.code),
                        components.FormInput(self.form.name),
                    ],
                )
            ]
        )


class CountryIndexView(components.IndexView[Country]):
    def build(self, request: Request) -> components.Component:
        return components.Table(
            items=self.models,
            header=components.TableRow(
                children=[
                    components.TableSortableHeadCell("Code", sort_field="code"),
                    components.TableHeadCell("Name"),
                ]
            ),
            row_builder=lambda row: components.TableRow(
                children=[
                    components.TableColumn(
                        row.code,
                        value_builder=lambda: components.Link(
                            text=str(row), url=CountryResource.get_edit_page_route(row.code)
                        ),
                    ),
                    components.TableColumn(row.name),
                ]
            ),
        )


class CountryResource(ResourceScreen):
    group = "Shop"
    icon = icons.ICON_COUNTRIES
    datasource = SADataSource(Country)
    form_class = CountryForm
    index_view_class = CountryIndexView
    detail_view_class = CountryDetailView
    form_view_class = FormView
    ordering_fields = ("code",)
