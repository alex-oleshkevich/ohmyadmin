import wtforms
from starlette.requests import Request

from examples.admin.products import ProductForm
from ohmyadmin import layouts
from ohmyadmin.pages.form import FormPage


class SimpleLayout(FormPage):
    label = 'Simlple layout'
    group = 'Form layouts'
    icon = 'cards'
    form_class = ProductForm

    def build_form_layout(self, request: Request, form: wtforms.Form) -> layouts.Layout:
        return layouts.Card(
            [
                layouts.RowFormLayout(
                    label='Vertical layout',
                    description='Form fields are in horizontal layout where labels at left side.',
                    children=[layouts.Input(field) for field in form],
                )
            ]
        )
