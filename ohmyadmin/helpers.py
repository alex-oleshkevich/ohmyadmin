import dataclasses

import inspect
import re
import typing
from starlette.datastructures import URL
from starlette.requests import Request


def camel_to_sentence(text: str) -> str:
    """
    Convert camel cased strings (like class names) into a sentence.

    Example: OrderItemsResource -> Order items resource.
    """
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', text)


def snake_to_sentence(text: str) -> str:
    return text.replace('_', ' ')


def pluralize(text: str) -> str:
    """
    A simple pluralization utility.

    It adds -ies suffix to any noun that ends with -y, it adds -es suffix to any
    noun that ends with -s. For all other cases it appends -s.
    """
    if text.endswith('y'):
        return text[:-1] + 'ies'
    if text.endswith('s'):
        return text + 'es'
    return text + 's'


@dataclasses.dataclass
class LazyURL:
    path_name: str
    path_params: dict[str, typing.Any] = dataclasses.field(default_factory=dict)

    def resolve(self, request: Request) -> URL:
        return URL(request.url_for(self.path_name, **self.path_params))


class LazyObjectURL:
    def __init__(self, factory: typing.Callable[[Request, typing.Any], URL]) -> None:
        self.factory = factory

    def resolve(self, request: Request, obj: typing.Any) -> URL:
        return self.factory(request, obj)


def resolve_url(request: Request, url: str | URL | LazyURL) -> URL:
    if isinstance(url, LazyURL):
        return url.resolve(request)
    return URL(str(url))


def get_callable_name(obj: typing.Any) -> str:
    if inspect.isfunction(obj):
        return obj.__name__
    return obj.__class__.__name__
