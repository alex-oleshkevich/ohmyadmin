import typing
import wtforms
from starlette.requests import Request

from ohmyadmin.fields import Field


class FormElement:
    template: str = ''

    def render(self, request: Request) -> str:
        return request.state.admin.render(
            self.template,
            {
                'request': request,
                'element': self,
            },
        )

    __call__ = render


class Section(FormElement):
    template = 'ohmyadmin/forms/element_section.html'

    def __init__(self, elements: list[FormElement]) -> None:
        self.elements = elements

    def __iter__(self) -> typing.Iterator[FormElement]:
        return iter(self.elements)


class FormGroup(FormElement):
    template = 'ohmyadmin/forms/element_form_group.html'

    def __init__(self, field: Field, form_field: wtforms.Field) -> None:
        self.field = field
        self.form_field = form_field
