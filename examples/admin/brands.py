import typing
import wtforms
from starlette.requests import Request

from examples.models import Brand
from ohmyadmin import display, layout
from ohmyadmin.display import DisplayField
from ohmyadmin.ext.sqla import ChoiceFilter, SQLAlchemyResource
from ohmyadmin.filters import BaseFilter
from ohmyadmin.forms import BooleanField, Form, MarkdownField, SlugField, StringField, URLField
from ohmyadmin.layout import Card, FormElement, FormText, Grid, Group, LayoutComponent


class BrandResource(SQLAlchemyResource):
    icon = 'basket'
    entity_class = Brand

    def get_filters(self, request: Request) -> typing.Iterable[BaseFilter]:
        yield ChoiceFilter(
            Brand.website,
            choices=[
                ('http://simpson.com/', 'Simpson'),
                ('http://ross.com/', 'Ross'),
            ],
        )

    def get_list_fields(self) -> typing.Iterable[DisplayField]:
        yield DisplayField('name', searchable=True, sortable=True, link=True)
        yield DisplayField('website')
        yield DisplayField('visible_to_customers', label='Visibility', component=display.Boolean())
        yield DisplayField('updated_at', component=display.DateTime())

    def get_form_fields(self, request: Request) -> typing.Iterable[wtforms.Field]:
        yield StringField(name='name', validators=[wtforms.validators.DataRequired()])
        yield SlugField(name='slug', validators=[wtforms.validators.DataRequired()])
        yield URLField(name='website')
        yield BooleanField(name='visible_to_customers')
        yield MarkdownField(name='description')

    def get_form_layout(self, request: Request, form: Form, instance: typing.Any) -> LayoutComponent:
        return Grid(
            columns=3,
            children=[
                Group(
                    colspan=2,
                    children=[
                        Card(
                            columns=2,
                            children=[
                                'name',
                                'slug',
                                'website',
                                'visible_to_customers',
                                FormElement('description', colspan=2),
                            ],
                        ),
                    ],
                ),
                Group(
                    colspan=1,
                    children=[
                        Card(
                            children=[
                                FormText('Created at', layout.Date(instance.created_at)),
                                FormText('Updated at', layout.Date(instance.updated_at)),
                            ]
                        )
                    ],
                ),
            ],
        )
