import wtforms
from starlette.requests import Request

from examples import icons
from examples.models import Brand
from ohmyadmin import components, filters
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.resources.resource import ResourceScreen


class BrandForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])
    website = wtforms.URLField()
    visible_to_customers = wtforms.BooleanField()
    description = wtforms.TextAreaField()


class BrandDetailView(components.DetailView[Brand]):
    def build(self, request: Request) -> components.Component:
        return components.Column(
            [
                components.ModelField("Name", self.model.name),
                components.ModelField("Website", self.model.website),
                components.ModelField(
                    "Visible to customers",
                    self.model.visible_to_customers,
                    value_builder=lambda value: components.BoolValue(value=value),
                ),
                components.ModelField("Updated at", self.model.updated_at),
            ]
        )


class BrandFormView(components.FormView[BrandForm, Brand]):
    def build(self, request: Request) -> components.Component:
        return components.Grid(
            children=[
                components.Container(
                    colspan=5,
                    child=components.Column(
                        children=[
                            components.FormInput(self.form.name),
                            components.FormInput(self.form.slug),
                            components.FormInput(self.form.website),
                            components.FormInput(self.form.description, colspan=6),
                            components.FormInput(self.form.visible_to_customers),
                        ]
                    ),
                ),
            ],
        )


class BrandsIndexView(components.IndexView[Brand]):
    def build(self, request: Request) -> components.Component:
        return components.Table[Brand](
            items=self.models,
            header=components.TableRow(
                children=[
                    components.TableSortableHeadCell("Name", sort_field="name"),
                    components.TableHeadCell("Website"),
                    components.TableHeadCell("Visible to customers"),
                    components.TableHeadCell("Updated at"),
                ]
            ),
            row_builder=lambda row: components.TableRow(
                children=[
                    components.TableColumn(
                        value_builder=lambda: components.Link(
                            text=str(row), url=BrandResource.get_edit_page_route(row.id)
                        )
                    ),
                    components.TableColumn(
                        value_builder=lambda: components.Link(
                            url=row.website,
                            text=row.website,
                            target="_blank",
                        )
                    ),
                    components.TableColumn(value_builder=lambda: components.BoolValue(row.visible_to_customers)),
                    components.TableColumn(row.updated_at),
                ]
            ),
        )


class BrandResource(ResourceScreen):
    group = "Shop"
    icon = icons.ICON_BASKET
    datasource = SADataSource(Brand)
    form_class = BrandForm
    searchable_fields = ["name"]
    ordering_fields = ("name",)
    page_filters = [
        filters.ChoiceFilter(
            "website",
            choices=[
                ("http://simpson.com/", "Simpson"),
                ("http://ross.com/", "Ross"),
                ("https://www.sanders.net/", "Sanders"),
            ],
        ),
    ]

    index_view_class = BrandsIndexView
    detail_view_class = BrandDetailView
    form_view_class = BrandFormView
