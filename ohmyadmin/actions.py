import dataclasses

import typing
from starlette.requests import Request

from ohmyadmin.layout import View


@dataclasses.dataclass
class LinkAction(View):
    text: str
    url: str
    icon: str = ''

    def render(self, request: Request) -> str:
        return super().render(request)


@dataclasses.dataclass
class ConfirmAction:
    title: str
    action_url: str
    message: str = ''
    dangerous: bool = False
    method: typing.Literal['get', 'post'] = 'post'


@dataclasses.dataclass
class Action:
    @classmethod
    def link(cls, text: str, url: str, icon: str = '') -> LinkAction:
        return LinkAction(text=text, url=url, icon=icon)

    @classmethod
    def confirm(
        cls,
        title: str,
        action_url: str,
        message: str = '',
        dangerous: bool = False,
        method: typing.Literal['get', 'post'] = 'post',
    ) -> ConfirmAction:
        return ConfirmAction(title=title, message=message, dangerous=dangerous, action_url=action_url, method=method)
