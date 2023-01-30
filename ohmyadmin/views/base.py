import abc
import typing
from starlette.requests import Request

from ohmyadmin.pagination import Pagination


class IndexView:
    @abc.abstractmethod
    def render(self, request: Request, objects: Pagination[typing.Any]) -> str:  # pragma: no cover
        ...
