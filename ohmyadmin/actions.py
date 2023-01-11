import abc
from starlette.requests import Request

from ohmyadmin.shortcuts import render_to_string


class Action(abc.ABC):
    label: str = ''
    icon: str = ''
    template: str = ''

    def render(self, request: Request) -> str:
        return render_to_string(request, self.template, {'action': self})
