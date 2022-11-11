import typing
import wtforms
from starlette.requests import Request

from examples.models import BlogPost, Category, User
from ohmyadmin import rich_text
from ohmyadmin.display import DisplayField
from ohmyadmin.ext.sqla import SQLAlchemyResource, choices_from
from ohmyadmin.forms import Form, RichTextField, SelectField, StringField
from ohmyadmin.layout import Card, FormElement, Grid, LayoutComponent
from ohmyadmin.rich_text import EditorToolbar


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
        yield StringField(name='title', validators=[wtforms.validators.data_required()])
        yield RichTextField(
            name='content',
            toolbar=EditorToolbar(
                [
                    rich_text.Bold(),
                    rich_text.Italic(),
                    rich_text.Quote(),
                    rich_text.BulletList(),
                    rich_text.OrderedList(),
                    rich_text.Code(),
                    rich_text.CodeBlock(),
                    rich_text.Separator(),
                    rich_text.Link(),
                    rich_text.Highlight(),
                    rich_text.Heading(),
                ]
            ),
        )
        yield SelectField(name='author_id', choices=choices_from(User, label_column='full_name'), coerce=safe_int)

    def get_form_layout(self, request: Request, form: Form, instance: Category) -> LayoutComponent:
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
