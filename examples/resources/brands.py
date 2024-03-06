import wtforms
from starlette.requests import Request
from starlette_babel import gettext_lazy as _

import ohmyadmin.components.layout
from examples import icons
from examples.models import Brand
from ohmyadmin import components, filters, formatters
from ohmyadmin.components import BaseFormLayoutBuilder
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.views.table import TableView


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


class _FormLayout(BaseFormLayoutBuilder):
    def build(self, form: BrandForm) -> components.Component:
        return ohmyadmin.components.layout.Grid(
            colspan=2,
            children=[
                ohmyadmin.components.layout.Column(
                    children=[
                        components.FormInput(form.name),
                        components.FormInput(form.slug),
                        components.FormInput(form.website),
                        components.FormInput(form.description, colspan=12),
                    ]
                ),
                ohmyadmin.components.layout.Column(
                    children=[
                        components.FormInput(form.visible_to_customers),
                    ]
                ),
            ],
        )


class BrandResource(ResourceScreen):
    group = "Shop"
    icon = icons.ICON_BASKET
    datasource = SADataSource(Brand)
    form_class = BrandForm
    searchable_fields = ["name"]
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

    detail_view_class = BrandDetailView
    index_view = TableView(
        [
            DisplayField("name", link=True),
            DisplayField("website"),
            DisplayField("visible_to_customers", _("Visibility"), formatter=formatters.BoolFormatter(as_text=True)),
            DisplayField("updated_at", formatter=formatters.DateTime()),
        ]
    )
