from __future__ import annotations

import typing

from ohmyadmin.helpers import render_to_string
from ohmyadmin.layout import View

ActionColor = typing.Literal['default', 'primary', 'text', 'danger']


class Action(View):
    pass


class LinkAction(Action):
    def __init__(self, url: str, text: str = '', icon: str = '', color: ActionColor = 'text') -> None:
        assert text or icon, 'Link requires either text or icon argument.'
        self.text = text
        self.url = url
        self.icon = icon
        self.color = color

    def render(self) -> str:
        return render_to_string('ohmyadmin/ui/action_link.html', {'action': self})
