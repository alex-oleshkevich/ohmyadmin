import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import joinedload
from starlette.requests import Request

from examples import icons
from examples.models import Category
from ohmyadmin import formatters
from ohmyadmin.datasources.sqlalchemy import load_choices, SADataSource
from ohmyadmin.forms.utils import safe_int_coerce
from ohmyadmin.resources.resource import ResourceScreen
from ohmyadmin.display_fields import DisplayField
from ohmyadmin.views.table import TableView


class CategoryForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])
    parent_id = wtforms.SelectField(coerce=safe_int_coerce)
    visible_to_customers = wtforms.BooleanField()
    description = wtforms.TextAreaField()


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
    display_fields = [
        DisplayField("name"),
        DisplayField(
            "parent",
            label="Parent",
            formatter=formatters.LinkFormatter(
                url=lambda r, v: r.url_for(r.state.resource.get_display_route_name(), object_id=v.id),
            ),
        ),
        DisplayField("visible_to_customers", formatter=formatters.BoolFormatter()),
        DisplayField("description"),
    ]

    async def init_form(self, request: Request, form: CategoryForm) -> None:
        await load_choices(request.state.dbsession, form.parent_id, sa.select(Category).order_by(Category.name))
