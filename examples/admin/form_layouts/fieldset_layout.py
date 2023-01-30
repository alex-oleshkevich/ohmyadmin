from starlette.requests import Request

from examples.admin.products import ProductForm
from ohmyadmin import layouts
from ohmyadmin.pages.form import FormPage


class FieldSetLayout(FormPage):
    label = 'Field set layout'
    group = 'Form layouts'
    icon = 'forms'
    form_class = ProductForm

    def build_form_layout(self, request: Request, form: ProductForm) -> layouts.Layout:
        return layouts.Column(
            [
                layouts.SideSection(
                    label='Field set layout',
                    description='Form fields grouped in a field set',
                    children=[
                        layouts.Input(form.name),
                        layouts.Input(form.slug),
                        layouts.Input(form.description),
                    ],
                ),
                layouts.SideSection(
                    label='Field set layout',
                    description='Form fields grouped in a field set',
                    children=[
                        layouts.Input(form.price),
                        layouts.Input(form.compare_at_price),
                        layouts.Input(form.cost_per_item),
                        layouts.Input(form.quantity),
                        layouts.Input(form.slug),
                    ],
                ),
            ]
        )
