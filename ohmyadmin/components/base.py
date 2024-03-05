from __future__ import annotations

import abc

from starlette.requests import Request

from ohmyadmin.templating import render_to_string


class BaseComponent(abc.ABC):
    @abc.abstractmethod
    def render(self, request: Request) -> str:
        raise NotImplementedError()


class Component(BaseComponent):
    template_name: str = ""

    def render(self, request: Request) -> str:
        assert self.template_name, f"Component {self.__class__} does not define template."
        return render_to_string(request, self.template_name, {"component": self})
