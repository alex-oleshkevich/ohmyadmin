import sqlalchemy as sa
import wtforms
from starlette.requests import Request

from examples.models import Category
from ohmyadmin import formatters
from ohmyadmin.datasources.sqlalchemy import load_choices, SADataSource
from ohmyadmin.forms.utils import safe_int_coerce
from ohmyadmin.resources.resource import ResourceView
from ohmyadmin.views.table import Column


class CategoryForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])
    parent_id = wtforms.SelectField(coerce=safe_int_coerce)
    visible_to_customers = wtforms.BooleanField()
    description = wtforms.TextAreaField()


class CategoryResource(ResourceView):
    group = "Shop"
    form_class = CategoryForm
    datasource = SADataSource(Category)
    columns = [
        Column("name"),
        Column("parent_id"),
        Column("visible_to_customers", formatter=formatters.BoolFormatter()),
    ]

    async def init_form(self, request: Request, form: CategoryForm) -> None:
        await load_choices(request.state.dbsession, form.parent_id, sa.select(Category).order_by(Category.name))
