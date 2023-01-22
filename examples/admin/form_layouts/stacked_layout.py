import wtforms
from starlette.requests import Request

from examples.admin.products import ProductForm
from ohmyadmin import layouts
from ohmyadmin.pages.form import FormPage


class StackedLayout(FormPage):
    label = 'Stacked layout'
    group = 'Form layouts'
    icon = 'cards'
    form_class = ProductForm

    def build_form_layout(self, request: Request, form: wtforms.Form) -> layouts.Layout:
        return layouts.Card(
            [
                layouts.StackedForm(
                    label='Stacked layout',
                    description='Form fields are centered and labels above the input.',
                    children=[layouts.Input(field) for field in form],
                )
            ]
        )
