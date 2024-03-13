from __future__ import annotations

import abc
import typing

import wtforms
from markupsafe import Markup
from starlette.requests import Request

from ohmyadmin.components.base import Component


class RawHTMLComponent(Component):
    def __init__(self, content: str) -> None:
        self.content = Markup(content)

    def render(self, request: Request) -> str:
        return self.content




class FormLayoutBuilder(typing.Protocol):
    def __call__(self, form: wtforms.Form | wtforms.Field) -> Component:
        ...


class BaseFormLayoutBuilder(abc.ABC):
    def __call__(self, form: wtforms.Form) -> Component:
        return self.build(form)

    @abc.abstractmethod
    def build(self, form: wtforms.Form | wtforms.Field) -> Component:
        raise NotImplementedError()
