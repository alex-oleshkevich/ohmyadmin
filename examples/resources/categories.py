import sqlalchemy as sa
import wtforms
from sqlalchemy.orm import joinedload
from starlette.requests import Request

import ohmyadmin.components.base
from examples import icons
from examples.models import Category
from ohmyadmin import components, formatters
from ohmyadmin.components import Component
from ohmyadmin.components.display import DetailView
from ohmyadmin.datasources.sqlalchemy import load_choices, SADataSource
from ohmyadmin.forms.utils import safe_int_coerce
from ohmyadmin.resources.resource import ResourceScreen


class CategoryForm(wtforms.Form):
    name = wtforms.StringField(validators=[wtforms.validators.data_required()])
    slug = wtforms.StringField(validators=[wtforms.validators.data_required()])
    parent_id = wtforms.SelectField(coerce=safe_int_coerce)
    visible_to_customers = wtforms.BooleanField()
    description = wtforms.TextAreaField()


class CategoryDetailView(DetailView[Category]):
    def compose(self, request: Request) -> Component:
        return components.Column(
            [
                components.ModelField("Name", components.Text(self.model.name)),
                components.ModelField("Description", components.Text(self.model.description)),
                components.ModelField(
                    "Parent",
                    ohmyadmin.components.base.When(
                        expression=self.model.parent_id,
                        when_true=components.Builder(
                            builder=lambda: components.Link(
                                url=CategoryResource.get_display_page_route(self.model.parent.id),
                                text=self.model.parent.name,
                            )
                        ),
                        when_false=components.Text(),
                    ),
                ),
                components.ModelField(
                    "Visible to customers",
                    components.BoolValue(self.model.visible_to_customers),
                ),
                components.ModelField(
                    "Created at",
                    components.Text(
                        self.model.created_at,
                        formatter=formatters.DateTime(),
                    ),
                ),
                components.ModelField(
                    "Updated at", components.Text(self.model.updated_at, formatter=formatters.DateTime())
                ),
            ]
        )


class CategoryFormView(components.FormView[CategoryForm, Category]):
    def compose(self, request: Request) -> Component:
        return components.Grid(
            children=[
                components.Column(
                    colspan=6,
                    children=[
                        components.FormInput(self.form.name),
                        components.FormInput(self.form.parent_id),
                        components.FormInput(self.form.visible_to_customers),
                        components.FormInput(self.form.description),
                        components.FormInput(self.form.slug),
                    ],
                )
            ]
        )


class CategoryIndexView(components.IndexView[Category]):
    def compose(self, request: Request) -> Component:
        return components.Table(
            items=self.models,
            header=components.TableRow(
                children=[
                    components.TableSortableHeadCell("Name", sort_field="name"),
                    components.TableHeadCell("Parent"),
                    components.TableHeadCell("Visible to customers"),
                ]
            ),
            row_builder=lambda row: components.TableRow(
                children=[
                    components.TableColumn(
                        child=components.Link(text=row.name, url=CategoryResource.get_edit_page_route(row.id))
                    ),
                    components.TableColumn(
                        child=ohmyadmin.components.base.When(
                            expression=row.parent_id,
                            when_true=components.Builder(
                                builder=lambda: components.Link(
                                    text=row.parent.name,
                                    url=CategoryResource.get_edit_page_route(row.parent_id),
                                )
                            ),
                            when_false=components.Text(),
                        ),
                    ),
                    components.TableColumn(child=components.BoolValue(row.visible_to_customers)),
                ]
            ),
        )


class CategoryResource(ResourceScreen):
    group = "Shop"
    icon = icons.ICON_CATEGORY
    form_class = CategoryForm
    datasource = SADataSource(
        Category,
        query=(sa.select(Category).options(joinedload(Category.parent)).order_by(Category.name.asc())),
    )
    index_view_class = CategoryIndexView
    detail_view_class = CategoryDetailView
    form_view_class = CategoryFormView
    ordering_fields = ("name",)

    async def init_form(self, request: Request, form: CategoryForm) -> None:
        await load_choices(request.state.dbsession, form.parent_id, sa.select(Category).order_by(Category.name))
