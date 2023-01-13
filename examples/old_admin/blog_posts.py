import typing
import wtforms
from starlette.requests import Request

from examples.models import BlogPost, Category, User
from ohmyadmin.display import DisplayField
from ohmyadmin.ext.sqla import SQLAlchemyResource, choices_from
from ohmyadmin.forms import AsyncForm, AsyncSelectField, TrixField
from ohmyadmin.layout import Card, FormElement, Grid, LayoutComponent


def safe_int(value: int | str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


class BlogPostResource(SQLAlchemyResource):
    icon = 'article'
    group = 'Blog'
    entity_class = BlogPost

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        yield DisplayField('title', searchable=True, sortable=True, link=True)

    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        yield wtforms.StringField(name='title', validators=[wtforms.validators.data_required()])
        yield TrixField(name='content')
        yield AsyncSelectField(name='author_id', choices=choices_from(User, label_column='full_name'), coerce=safe_int)

    def get_form_layout(self, request: Request, form: AsyncForm, instance: Category) -> LayoutComponent:
        return Grid(
            columns=1,
            children=[
                Card(
                    columns=1,
                    children=[
                        FormElement(form.title),
                        FormElement(form.author_id),
                        FormElement(form.content),
                    ],
                )
            ],
        )
