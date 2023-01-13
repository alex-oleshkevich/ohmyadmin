import typing
import wtforms
from starlette.requests import Request

from examples.models import Category
from ohmyadmin import display
from ohmyadmin.display import DisplayField
from ohmyadmin.ext.sqla import SQLAlchemyResource, choices_from
from ohmyadmin.forms import AsyncForm, AsyncSelectField
from ohmyadmin.layout import Card, Date, FormElement, FormText, Grid, Group, LayoutComponent


def safe_int(value: int | str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


class CategoryResource(SQLAlchemyResource):
    icon = 'category'
    entity_class = Category

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        yield DisplayField('name', searchable=True, sortable=True, link=True)
        yield DisplayField('visible_to_customers', label='Visilibity', component=display.Boolean())
        yield DisplayField('updated_at', component=display.DateTime())

    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        yield wtforms.StringField(name='name', validators=[wtforms.validators.data_required()])
        yield wtforms.StringField(name='slug', validators=[wtforms.validators.data_required()])
        yield AsyncSelectField(name='parent_id', choices=choices_from(Category), coerce=safe_int)
        yield wtforms.BooleanField(name='visible_to_customers')
        yield wtforms.TextAreaField(name='description')

    def get_form_layout(self, request: Request, form: AsyncForm, instance: Category) -> LayoutComponent:
        return Grid(
            columns=3,
            children=[
                Group(
                    colspan=2,
                    children=[
                        Card(
                            columns=2,
                            children=[
                                FormElement(form.name),
                                FormElement(form.slug),
                                FormElement(form.parent_id, colspan=2),
                                FormElement(form.visible_to_customers),
                                FormElement(form.description, colspan=2),
                            ],
                        )
                    ],
                ),
                Group(
                    colspan=1,
                    children=[
                        Card(
                            children=[
                                FormText('Created at', Date(instance.created_at)),
                                FormText('Updated at', Date(instance.updated_at)),
                            ]
                        )
                    ],
                ),
            ],
        )
