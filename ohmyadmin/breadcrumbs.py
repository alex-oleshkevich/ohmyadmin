import dataclasses
import typing

from starlette.datastructures import URL
from starlette.requests import Request

_URLFactory: typing.TypeAlias = typing.Callable[[Request], URL]


@dataclasses.dataclass
class Breadcrumb:
    label: str
    url: URL | str | _URLFactory = ""

    def get_url(self, request: Request) -> URL:
        if callable(self.url):
            return self.url(request)
        return URL(str(self.url)) if self.url else ""
