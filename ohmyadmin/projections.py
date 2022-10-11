import abc
import typing
from slugify import slugify

from ohmyadmin.helpers import camel_to_sentence


class ProjectionMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, typing.Any], **kwargs: typing.Any) -> typing.Type:
        if name != 'Projection':
            attrs['slug'] = attrs.get('id', slugify(camel_to_sentence(name.removesuffix('Projection'))))
            attrs['label'] = attrs.get('label', camel_to_sentence(name.removesuffix('Projection')))

        return super().__new__(cls, name, bases, attrs)


class Projection(metaclass=ProjectionMeta):
    slug: str = ''
    label: str = ''

    @abc.abstractmethod
    def apply(self, query: typing.Any) -> typing.Any:
        ...


class DefaultProjection(Projection):
    def __init__(self, query: typing.Any, label: str) -> None:
        self.slug = ''
        self.query = query
        self.label = label

    def apply(self, _: typing.Any) -> typing.Any:
        return self.query
