import typing
import wtforms
from starlette.requests import Request

from examples.models import Brand
from ohmyadmin.components import Card, Component, FormElement, FormPlaceholder, Grid, Group, display
from ohmyadmin.components.display import DisplayField
from ohmyadmin.ext.sqla import SelectFilter, SQLAlchemyResource
from ohmyadmin.filters import BaseFilter
from ohmyadmin.forms import BooleanField, Form, MarkdownField, SlugField, StringField, URLField


class BrandResource(SQLAlchemyResource):
    icon = 'basket'
    entity_class = Brand

    def get_filters(self, request: Request) -> typing.Iterable[BaseFilter]:
        yield SelectFilter(
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

    def get_form_layout(self, request: Request, form: Form) -> Component:
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
                                FormElement(form.website),
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
                                FormPlaceholder(
                                    'Created at',
                                    (
                                        form.instance.created_at.date().isoformat()
                                        if form.instance and form.instance.created_at
                                        else '-'
                                    ),
                                ),
                                FormPlaceholder(
                                    'Updated at',
                                    (
                                        form.instance.updated_at.date().isoformat()
                                        if form.instance and form.instance.updated_at
                                        else '-'
                                    ),
                                ),
                            ]
                        )
                    ],
                ),
            ],
        )
