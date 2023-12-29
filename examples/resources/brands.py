import wtforms
from starlette_babel import gettext_lazy as _

from examples.models import Brand
from ohmyadmin import components, filters, formatters
from ohmyadmin.components import BaseFormLayoutBuilder
from ohmyadmin.datasources.sqlalchemy import SADataSource
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.screens.table import Column
from ohmyadmin.views.table import TableView


class BrandForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])
    website = wtforms.URLField()
    visible_to_customers = wtforms.BooleanField()
    description = wtforms.TextAreaField()


class _FormLayout(BaseFormLayoutBuilder):
    def build(self, form: BrandForm) -> components.Component:
        return components.GridComponent(
            colspan=2,
            children=[
                components.ColumnComponent(
                    children=[
                        components.FormInput(form.name),
                        components.FormInput(form.slug),
                        components.FormInput(form.website),
                        components.FormInput(form.description, colspan=12),
                    ]
                ),
                components.ColumnComponent(
                    children=[
                        components.FormInput(form.visible_to_customers),
                    ]
                ),
            ],
        )


class BrandsResource(ResourceScreen):
    label = _("Brand")
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
    index_view = TableView(
        [
            Column("name"),
            Column("website"),
            Column("visible_to_customers", _("Visibility"), formatter=formatters.BoolFormatter(as_text=True)),
            Column("updated_at", formatter=formatters.DateTimeFormatter()),
        ]
    )
