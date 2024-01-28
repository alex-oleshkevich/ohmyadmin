import abc
import typing

from starlette.requests import Request

from ohmyadmin import components, display_fields
from ohmyadmin.components import DisplayLayoutBuilder
from ohmyadmin.templating import render_to_string


class DisplayView(typing.Protocol):
    def __call__(self, request: Request, model: object) -> str:
        ...


class BaseDisplayView(abc.ABC):
    @abc.abstractmethod
    def render(self, request: Request, model: object) -> components.Component:
        raise NotImplementedError()

    def __call__(self, request: Request, model: object) -> str:
        component = self.render(request, model)
        return component.render(request)


class BuilderDisplayView(BaseDisplayView):
    def __init__(self, builder: DisplayLayoutBuilder) -> None:
        self.builder = builder

    def render(self, request: Request, model: object) -> components.Component:
        return self.builder(request, model)


class AutoDisplayView(BaseDisplayView):
    def __init__(self, fields: typing.Sequence[display_fields.DisplayField]) -> None:
        self.fields = fields

    def render(self, request: Request, model: object) -> components.Component:
        return components.Grid(
            columns=12,
            children=[
                components.Column(
                    colspan=6,
                    children=[components.DisplayFieldComponent(field=field, model=model) for field in self.fields],
                )
            ],
        )


class TemplateDisplayView(BaseDisplayView):
    def __init__(self, template: str, context: typing.Mapping[str, typing.Any] | None = None) -> None:
        self.template = template
        self.context = context or {}

    def __call__(self, request: Request, model: object) -> str:
        context = self.context
        context.update({"model": model})
        return render_to_string(request, self.template, context)
