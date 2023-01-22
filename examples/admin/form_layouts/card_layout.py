import wtforms
from starlette.requests import Request

from examples.admin.products import ProductForm
from ohmyadmin import layouts
from ohmyadmin.pages.form import FormPage


class CardLayout(FormPage):
    label = 'Card layout'
    group = 'Form layouts'
    icon = 'cards'
    form_class = ProductForm

    def build_form_layout(self, request: Request, form: wtforms.Form) -> layouts.Layout:
        return layouts.Card(
            label='Card layout',
            description='Form fields grouped in a card',
            children=[layouts.Input(field) for field in form],
        )
