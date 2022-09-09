from __future__ import annotations

import typing

from ohmyadmin.helpers import render_to_string

ActionColor = typing.Literal['default', 'primary', 'text', 'danger']


class Action:
    template = ''

    def render(self) -> str:
        assert self.template, 'Template for action is not defined'
        return render_to_string(self.template, {'action': self})

    __call__ = render
    __str__ = render


class SubmitAction(Action):
    template = 'ohmyadmin/ui/action_submit.html'

    def __init__(self, text: str, icon: str = '', color: ActionColor = 'default', name: str | None = '') -> None:
        self.text = text
        self.icon = icon
        self.color = color
        self.name = name


class LinkAction(Action):
    def __init__(self, url: str, text: str = '', icon: str = '', color: ActionColor = 'text') -> None:
        assert text or icon, 'Link requires either text or icon argument.'
        self.text = text
        self.url = url
        self.icon = icon
        self.color = color

    def render(self) -> str:
        return render_to_string('ohmyadmin/ui/action_link.html', {'action': self})
