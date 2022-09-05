from __future__ import annotations

import typing
from starlette.requests import Request

from ohmyadmin.helpers import render_to_string
from ohmyadmin.layout import View

ActionColor = typing.Literal['default', 'primary', 'text', 'danger']


class Action(View):
    pass


class LinkAction(Action):
    def __init__(self, text: str, url: str, icon: str = '', color: ActionColor = 'text') -> None:
        self.text = text
        self.url = url
        self.icon = icon
        self.color = color

    def render(self, request: Request) -> str:
        return render_to_string(request, 'ohmyadmin/ui/action_link.html', {'action': self})
