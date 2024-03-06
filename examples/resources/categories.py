import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import joinedload
from starlette.requests import Request

from examples import icons
from examples.models import Category
from ohmyadmin import components, formatters
from ohmyadmin.components import Component
from ohmyadmin.components.display import DetailView
from ohmyadmin.datasources.sqlalchemy import load_choices, SADataSource
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.forms.utils import safe_int_coerce
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.views.table import TableView


class CategoryForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])
    parent_id = wtforms.SelectField(coerce=safe_int_coerce)
    visible_to_customers = wtforms.BooleanField()
    description = wtforms.TextAreaField()


class CategoryDetailView(DetailView[Category]):
    def build(self, request: Request) -> Component:
        return components.Column(
            [
                components.ModelField("Name", self.model.name),
                components.ModelField("Description", self.model.description),
                components.ModelField(
                    "Parent",
                    value=self.model.parent,
                    value_builder=(
                        lambda _: components.Link(
                            url=CategoryResource.get_display_page_route(self.model.parent.id),
                            text=self.model.parent.name,
                        )
                    )
                    if self.model.parent
                    else None,
                ),
                components.ModelField(
                    "Visible to customers",
                    self.model.visible_to_customers,
                    value_builder=lambda value: components.BoolValue(value, as_text=False),
                ),
                components.ModelField("Created at", self.model.created_at),
                components.ModelField("Updated at", self.model.updated_at),
            ]
        )


class CategoryResource(ResourceScreen):
    group = "Shop"
    icon = icons.ICON_CATEGORY
    form_class = CategoryForm
    datasource = SADataSource(
        Category, query=(sa.select(Category).options(joinedload(Category.parent)).order_by(Category.name.asc()))
    )
    index_view = TableView(
        columns=[
            DisplayField("name", link=True),
            DisplayField(
                "parent",
                label="Parent",
                formatter=formatters.LinkFormatter(
                    url=lambda r, v: r.url_for(r.state.resource.get_display_route_name(), object_id=v.id),
                ),
            ),
            DisplayField("visible_to_customers", label="Visibility", formatter=formatters.BoolFormatter()),
        ]
    )
    detail_view_class = CategoryDetailView

    async def init_form(self, request: Request, form: CategoryForm) -> None:
        await load_choices(request.state.dbsession, form.parent_id, sa.select(Category).order_by(Category.name))
