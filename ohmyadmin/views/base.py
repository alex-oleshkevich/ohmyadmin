import abc
import typing

from starlette.requests import Request


class IndexView:
    @abc.abstractmethod
    def render(self, request: Request, objects: list[typing.Any]) -> str: ...
