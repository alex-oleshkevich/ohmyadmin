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
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', text).lower().capitalize()


def snake_to_sentence(text: str) -> str:
    """Convert snake_case string into 'Snake case' sentence."""
    return text.replace('_', ' ').lower().capitalize()


uncountable = [
    'audio',
    'bison',
    'cattle',
    'chassis',
    'compensation',
    'coreopsis',
    'data',
    'deer',
    'education',
    'emoji',
    'equipment',
    'evidence',
    'feedback',
    'firmware',
    'fish',
    'furniture',
    'gold',
    'hardware',
    'information',
    'jedi',
    'kin',
    'knowledge',
    'love',
    'metadata',
    'money',
    'moose',
    'news',
    'nutrition',
    'offspring',
    'plankton',
    'pokemon',
    'police',
    'rain',
    'rice',
    'series',
    'sheep',
    'software',
    'species',
    'swine',
    'traffic',
    'wheat',
]


def pluralize(text: str) -> str:
    """
    A simple pluralization utility.

    It adds -ies suffix to any noun that ends with -y, it adds -es suffix to any noun that ends with -s. For all other
    cases it appends -s.
    """
    if text in uncountable:
        return text

    # is already plural?
    if text.endswith('ies') or text.endswith('rs') or text.endswith('ds'):
        return text

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
    if inspect.isclass(obj):
        return obj.__name__
    if inspect.ismethod(obj):
        return obj.__name__
    raise ValueError('Unsupported')
