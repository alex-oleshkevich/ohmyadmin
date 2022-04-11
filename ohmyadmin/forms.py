import typing
import wtforms
from starlette.requests import Request


class Form(wtforms.Form):
    async def validate_on_submit(self, request: Request) -> bool:
        return True


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

    def __init__(self, elements: list[FormElement], title: str, description: str = '') -> None:
        self.elements = elements
        self.title = title
        self.description = description

    def __iter__(self) -> typing.Iterator[FormElement]:
        return iter(self.elements)


class SectionRow(FormElement):
    template = 'ohmyadmin/forms/element_section_row.html'

    def __init__(self, field: wtforms.Field) -> None:
        self.field = field
